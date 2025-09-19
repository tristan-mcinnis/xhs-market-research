#!/usr/bin/env python3
"""
Master Pipeline Runner
Orchestrates the complete analysis workflow from scraping to visualization
"""

import os
import sys
import argparse
import json
import shlex
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# Import workflow configuration
from workflow_config import WorkflowConfig, get_workflow_config

# Pipeline steps info
PIPELINE_STEPS = {
    1: {
        'name': 'XHS Scraper',
        'script': 'step1_xhs_scraper.py',
        'description': 'Scrape posts and images from Xiaohongshu',
        'output_dir': 'step1_scraped',
        'required': True
    },
    2: {
        'name': 'Semiotic Analysis',
        'script': 'step2_semiotic_analysis.py',
        'description': 'Analyze images using GPT-5-mini for semiotic insights',
        'output_dir': 'step2_analyses',
        'required': True,
        'needs_api_key': 'OPENAI_API_KEY'
    },
    3: {
        'name': 'Clustering',
        'script': 'step3_clustering.py',
        'description': 'Cluster analyses into thematic groups',
        'output_dir': 'step3_clusters',
        'required': False
    },
    4: {
        'name': 'Comparative Analysis',
        'script': 'step4_comparative_analysis.py',
        'description': 'Compare patterns across groups',
        'output_dir': 'step4_comparative',
        'required': False
    },
    5: {
        'name': 'Insight Extraction',
        'script': 'step5_insight_extraction.py',
        'description': 'Extract rich insights using GPT-5-mini',
        'output_dir': 'step5_insights',
        'required': False,
        'needs_api_key': 'OPENAI_API_KEY'
    },
    6: {
        'name': 'Theme Enrichment',
        'script': 'step6_theme_enrichment.py',
        'description': 'Generate detailed themes from clusters',
        'output_dir': 'step6_themes',
        'required': False,
        'needs_api_key': 'OPENAI_API_KEY'
    },
    7: {
        'name': 'Visualization',
        'script': 'step7_visualization.py',
        'description': 'Create visual outputs and brand playbook',
        'output_dir': 'step7_visualizations',
        'required': False
    }
}


class PipelineRunner:
    """Orchestrates the analysis pipeline"""

    def __init__(self, config: WorkflowConfig, verbose: bool = False):
        self.config = config
        self.verbose = verbose
        self.results = {}

    def check_dependencies(self) -> bool:
        """Check if all required dependencies are available"""
        print("\n🔍 Checking dependencies...")

        # Check for required API keys
        missing_keys = []
        for step_info in PIPELINE_STEPS.values():
            if 'needs_api_key' in step_info:
                key_name = step_info['needs_api_key']
                if not os.getenv(key_name):
                    missing_keys.append(key_name)

        if missing_keys:
            print(f"❌ Missing API keys: {', '.join(missing_keys)}")
            print("Please add them to your .env file")
            return False

        # Check for Python packages
        required_packages = [
            'apify_client', 'requests', 'pandas', 'numpy',
            'scikit-learn', 'sentence_transformers', 'matplotlib', 'openai'
        ]

        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            print(f"❌ Missing packages: {', '.join(missing_packages)}")
            print("Please run: ./setup.sh or pip install -r requirements.txt")
            return False

        print("✅ All dependencies satisfied")
        return True

    def run_step(self, step_num: int, **kwargs) -> bool:
        """Run a specific pipeline step"""
        if step_num not in PIPELINE_STEPS:
            print(f"❌ Invalid step number: {step_num}")
            return False

        step_info = PIPELINE_STEPS[step_num]
        print(f"\n{'='*60}")
        print(f"Step {step_num}: {step_info['name']}")
        print(f"{'='*60}")
        print(f"📝 {step_info['description']}")

        # Build command based on step
        script = step_info['script']

        if step_num == 1:  # XHS Scraper
            query = kwargs.get('query', self.config.query)
            max_items = kwargs.get('max_items', 30)
            download = kwargs.get('download', True)
            scraped_dir = self.config.get_dir('step1_scraped')
            images_dir = self.config.get_dir('step1_images')
            query_dir = self.config.query_dir

            cmd_parts = [
                "python",
                script,
                "search",
                shlex.quote(query),
                "--max-items",
                str(max_items),
                "--scraped-dir",
                shlex.quote(str(scraped_dir)),
                "--images-dir",
                shlex.quote(str(images_dir)),
                "--query-dir",
                shlex.quote(str(query_dir)),
                "--date",
                shlex.quote(self.config.date),
            ]

            if download:
                cmd_parts.append("--download")

            cmd = " ".join(cmd_parts)

        elif step_num == 2:  # Semiotic Analysis
            images_dir = self.config.get_dir('step1_images')
            output_dir = self.config.get_dir('step2_analyses')

            cmd = f"python {script} --image-dir '{images_dir}' --output-dir '{output_dir}'"
            if kwargs.get('synthesize'):
                cmd += " --synthesize"

        elif step_num == 3:  # Clustering
            input_dir = self.config.get_dir('step2_analyses')
            output_dir = self.config.get_dir('step3_clusters')

            cmd = f"python {script} --input-dir '{input_dir}' --out-dir '{output_dir}'"
            cmd += f" --k-min {kwargs.get('k_min', 3)} --k-max {kwargs.get('k_max', 10)}"

        elif step_num == 4:  # Comparative Analysis
            input_dir = self.config.get_dir('step2_analyses')
            output_dir = self.config.get_dir('step4_comparative')

            cmd = f"python {script} --json-dir '{input_dir}' --out-dir '{output_dir}'"
            cmd += f" --top-k {kwargs.get('top_k', 20)}"

        elif step_num == 5:  # Insight Extraction
            input_dir = self.config.get_dir('step2_analyses')
            output_dir = self.config.get_dir('step5_insights')

            cmd = f"python {script} --json-dir '{input_dir}' --out-dir '{output_dir}'"
            if kwargs.get('synthesize', True):
                cmd += " --synthesize"

        elif step_num == 6:  # Theme Enrichment
            cluster_dir = self.config.get_dir('step3_clusters')
            analysis_dir = self.config.get_dir('step2_analyses')
            output_dir = self.config.get_dir('step6_themes')

            cmd = f"python {script} --cluster-dir '{cluster_dir}' --analysis-dir '{analysis_dir}'"
            cmd += f" --output-dir '{output_dir}'"
            if kwargs.get('synthesize', True):
                cmd += " --synthesize"

        elif step_num == 7:  # Visualization
            analysis_dir = self.config.get_dir('step2_analyses')

            # Try to find codebook from step 5 (insights)
            insights_dir = self.config.get_dir('step5_insights')
            codebook_path = insights_dir / 'codebook.csv'

            # If not found, look for KeyBERT version
            if not codebook_path.exists():
                codebook_path = insights_dir / 'codebook_patterns.csv'

            # If still not found, skip this step
            if not codebook_path.exists():
                print(f"⚠️  No codebook found. Run step 5 first or use KeyBERT version.")
                return False

            output_dir = self.config.get_dir('step7_visualizations')

            cmd = f"python {script} --json-dir '{analysis_dir}' --codebook '{codebook_path}'"
            cmd += f" --out-dir '{output_dir}' --top-per-section {kwargs.get('top_per_section', 15)}"

        else:
            print(f"❌ Step {step_num} not implemented")
            return False

        # Execute command
        print(f"\n🚀 Running: {cmd}\n")

        import subprocess
        try:
            # Activate virtual environment if it exists
            if Path('.venv').exists():
                if sys.platform == 'win32':
                    activate_cmd = '.venv\\Scripts\\activate && '
                else:
                    activate_cmd = 'source .venv/bin/activate && '
                cmd = activate_cmd + cmd

            result = subprocess.run(cmd, shell=True, capture_output=False, text=True)

            if result.returncode == 0:
                print(f"\n✅ Step {step_num} completed successfully")
                self.results[step_num] = {
                    'status': 'success',
                    'output_dir': self.config.get_dir(step_info['output_dir'])
                }
                return True
            else:
                print(f"\n❌ Step {step_num} failed with exit code {result.returncode}")
                self.results[step_num] = {'status': 'failed'}
                return False

        except Exception as e:
            print(f"\n❌ Error running step {step_num}: {e}")
            self.results[step_num] = {'status': 'error', 'error': str(e)}
            return False

    def run_pipeline(self, start_step: int = 1, end_step: int = 7, **kwargs) -> bool:
        """Run the complete pipeline or a subset of steps"""
        print(f"\n🎯 Running pipeline for query: '{self.config.query}'")
        print(f"📁 Working directory: {self.config.query_dir}")

        # Save configuration
        self.config.save_config()

        # Check dependencies
        if not self.check_dependencies():
            return False

        # Run each step
        for step_num in range(start_step, end_step + 1):
            if step_num in PIPELINE_STEPS:
                success = self.run_step(step_num, **kwargs)

                if not success and PIPELINE_STEPS[step_num]['required']:
                    print(f"\n❌ Pipeline stopped at required step {step_num}")
                    return False

                # Add delay between API-heavy steps
                if step_num in [2, 5, 6]:
                    import time
                    time.sleep(2)

        # Generate final report
        self.generate_report()
        return True

    def generate_report(self):
        """Generate a summary report of the pipeline run"""
        report_path = self.config.query_dir / "pipeline_report.md"

        with open(report_path, 'w') as f:
            f.write(f"# Pipeline Report\n\n")
            f.write(f"**Query:** {self.config.query}\n")
            f.write(f"**Date:** {self.config.date}\n")
            f.write(f"**Timestamp:** {datetime.now().isoformat()}\n\n")

            f.write("## Steps Executed\n\n")
            for step_num, result in self.results.items():
                step_info = PIPELINE_STEPS[step_num]
                status = result['status']
                emoji = "✅" if status == "success" else "❌"

                f.write(f"{emoji} **Step {step_num}: {step_info['name']}**\n")
                f.write(f"   - Status: {status}\n")

                if 'output_dir' in result:
                    f.write(f"   - Output: {result['output_dir']}\n")

                if 'error' in result:
                    f.write(f"   - Error: {result['error']}\n")

                f.write("\n")

            f.write("## Output Directories\n\n")
            for name, path in self.config.dirs.items():
                if path.exists() and any(path.iterdir()):
                    f.write(f"- {name}: `{path}`\n")

        print(f"\n📊 Report saved to: {report_path}")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='Run the complete XHS analysis pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('query', nargs='?', help='Query/topic to analyze')
    parser.add_argument('--start-step', type=int, default=1,
                        help='Starting step (default: 1)')
    parser.add_argument('--end-step', type=int, default=7,
                        help='Ending step (default: 7)')
    parser.add_argument('--max-items', type=int, default=30,
                        help='Max items to scrape (step 1)')
    parser.add_argument('--no-download', action='store_true',
                        help='Skip image download (step 1)')
    parser.add_argument('--k-min', type=int, default=3,
                        help='Min clusters (step 3)')
    parser.add_argument('--k-max', type=int, default=10,
                        help='Max clusters (step 3)')
    parser.add_argument('--date', help='Date string (YYYYMMDD format)')
    parser.add_argument('--continue-workflow', action='store_true',
                        help='Continue from existing workflow')
    parser.add_argument('--verbose', action='store_true',
                        help='Verbose output')

    args = parser.parse_args()

    # Load .env file
    from dotenv import load_dotenv
    load_dotenv()

    # Get or create workflow configuration
    if args.continue_workflow:
        from workflow_config import find_latest_workflow
        config = find_latest_workflow()
        if not config:
            print("❌ No existing workflow found")
            return
        print(f"📂 Continuing workflow: {config.query}")
    else:
        if not args.query:
            parser.print_help()
            print("\n❌ Error: Query is required for new workflow")
            print("Example: python run_pipeline.py '咖啡味避孕套'")
            return

        config = WorkflowConfig(query=args.query, date=args.date)

    # Create pipeline runner
    runner = PipelineRunner(config, verbose=args.verbose)

    # Run pipeline
    success = runner.run_pipeline(
        start_step=args.start_step,
        end_step=args.end_step,
        query=args.query or config.query,
        max_items=args.max_items,
        download=not args.no_download,
        k_min=args.k_min,
        k_max=args.k_max,
        synthesize=True
    )

    if success:
        print("\n🎉 Pipeline completed successfully!")
        print(f"📁 All outputs in: {config.query_dir}")
    else:
        print("\n⚠️  Pipeline completed with some failures")
        print("Check the report for details")


if __name__ == "__main__":
    main()