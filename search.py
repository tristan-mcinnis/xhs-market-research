#!/usr/bin/env python3
"""
Quick interactive search builder for Xiaohongshu
Simplified version for fast query building
"""

import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich import box

console = Console()


def main():
    console.clear()
    console.print(Panel(
        "[bold cyan]🔍 Quick Search Builder[/bold cyan]\n"
        "Build your Xiaohongshu search in seconds",
        box=box.ROUNDED,
        border_style="cyan"
    ))

    # Quick strategy selection
    console.print("\n[bold yellow]What are you searching for?[/bold yellow]\n")
    console.print("  [1] Single topic (e.g., '杜蕾斯 口味')")
    console.print("  [2] Multiple brands/competitors")
    console.print("  [3] Topic + variations (e.g., brand + different attributes)")
    console.print("  [4] Custom search list")

    choice = Prompt.ask("\n[cyan]Choice[/cyan]", choices=["1", "2", "3", "4"], default="1")

    queries = []
    combine = False

    if choice == "1":
        # Single query
        query = Prompt.ask("\n[yellow]Enter your search[/yellow]")
        queries = [query]

    elif choice == "2":
        # Multiple brands
        console.print("\n[yellow]Enter brand/competitor names:[/yellow]")
        console.print("[dim](Type each, press Enter. Empty line when done)[/dim]")

        while True:
            brand = Prompt.ask(f"  Brand {len(queries) + 1}", default="")
            if not brand:
                if queries:
                    break
                console.print("[red]Add at least one brand![/red]")
            else:
                queries.append(brand)

        combine = Confirm.ask("\n[yellow]Combine for comparison?[/yellow]", default=True)

    elif choice == "3":
        # Base + variations
        base = Prompt.ask("\n[yellow]Base term (e.g., brand)[/yellow]")
        console.print("\n[yellow]Add variations:[/yellow]")
        console.print("[dim](e.g., 口味, 价格, 质量 - empty line when done)[/dim]")

        variations = []
        while True:
            var = Prompt.ask(f"  Variation {len(variations) + 1}", default="")
            if not var:
                if variations:
                    break
                console.print("[red]Add at least one variation![/red]")
            else:
                variations.append(var)

        queries = [f"{base} {var}" for var in variations]
        combine = True

    else:
        # Custom
        console.print("\n[yellow]Enter searches:[/yellow]")
        console.print("[dim](One per line, empty line when done)[/dim]")

        while True:
            query = Prompt.ask(f"  Search {len(queries) + 1}", default="")
            if not query:
                if queries:
                    break
                console.print("[red]Add at least one search![/red]")
            else:
                queries.append(query)

        if len(queries) > 1:
            combine = Confirm.ask("\n[yellow]Combine results?[/yellow]", default=False)

    # Posts count
    posts = IntPrompt.ask(
        "\n[yellow]Posts per search[/yellow]",
        default=10
    )

    # Build command
    if len(queries) == 1:
        cmd = f'python main.py --keyword "{queries[0]}" --posts {posts}'
    else:
        queries_str = ' '.join(f'"{q}"' for q in queries)
        cmd = f'python scrape_multi.py {queries_str} --posts {posts}'
        if combine:
            cmd += ' --combine'

    # Summary
    console.print("\n" + "="*50)
    console.print(f"\n[bold green]Ready to search:[/bold green]")
    for q in queries:
        console.print(f"  • {q}")
    console.print(f"\n[dim]Total: {len(queries) * posts} posts[/dim]")

    # Execute
    console.print(f"\n[bold cyan]Command:[/bold cyan]\n[green]{cmd}[/green]")

    if Confirm.ask("\n[bold yellow]Run now?[/bold yellow]", default=True):
        console.print("\n[bold green]🚀 Starting...[/bold green]\n")
        try:
            subprocess.run(cmd, shell=True, check=True)
            console.print("\n[bold green]✅ Done![/bold green]")

            # Next steps
            console.print("\n[cyan]Next: Run analysis[/cyan]")
            if combine or len(queries) == 1:
                console.print("  python analyze.py --latest --themes --openai")
            else:
                console.print("  python analyze_multi.py")

        except subprocess.CalledProcessError:
            console.print("\n[red]Error during execution[/red]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled[/yellow]")
    else:
        console.print("\n[dim]Copy the command above to run manually[/dim]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")