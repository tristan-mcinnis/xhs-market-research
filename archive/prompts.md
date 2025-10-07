# Xiaohongshu Pipeline Prompts

This document contains all prompts used throughout the 7-step Xiaohongshu content analysis pipeline. All prompts are externalized in `pipeline_config.json` for easy modification without code changes.

---

## Step 2: Semiotic Analysis

**Purpose:** Analyze Xiaohongshu post images using GPT-5-mini to extract market insights across 5 dimensions.

### System Prompt

```
You are a market research analyst specializing in Chinese consumer behavior. You write your output primarily in English, making reference to important Chinese concepts and language when necessary. The images are from Xiaohongshu social commerce platform. Focus on extracting consumer insights and market signals.
```

### Main Analysis Prompt

```
Analyze this Xiaohongshu post for market insights. Be CONCISE — max 300 words.

1) CONSUMER BEHAVIOR: What is the user doing/sharing and why? What needs or desires does this reveal? (2–3 sentences)
2) MARKET SIGNALS: What products, services, or categories are featured? What purchasing decisions or considerations are evident? (2–3)
3) CULTURAL VALUES: What aspirations, anxieties, or lifestyle shifts does this represent? What does this say about modern Chinese consumers? (2–3)
4) EMOTIONAL DRIVERS: What feelings or social dynamics motivate this sharing? What problems are being solved? (2–3)
5) BRAND OPPORTUNITY: What unmet needs or white space does this suggest? What would resonate with this consumer? (1–2)

Return only the analysis text. Focus on WHY not HOW.
```

**Configuration:**
- Model: `gpt-5-mini`
- Max Output Tokens: `1200`
- Retry Max Tokens: `1800`
- Reasoning Effort: `medium`
- Verbosity: `medium`

### Corpus Synthesis Prompt

Used when `--synthesize` flag is provided to create a higher-level summary across all analyzed posts.

```
You are analyzing {count} Xiaohongshu posts about {topic}.

Below are market insights extracted from individual post analyses:

{corpus_summary}

Task: Produce a ~500-word synthesis with this structure (concise, high-signal), and return only the final text:

1. CONSUMER TRENDS (~100 words)
- What behaviors and needs are emerging?
- How are consumer priorities shifting?

2. MARKET OPPORTUNITIES (~100 words)
- What product/service gaps exist?
- What categories show growth potential?

3. CULTURAL SHIFTS (~100 words)
- What values and lifestyles are evolving?
- What does this reveal about modern Chinese society?

4. ECONOMIC INDICATORS (~100 words)
- What spending patterns are evident?
- What does this suggest about purchasing power and priorities?

5. STRATEGIC IMPLICATIONS (~100 words)
- What should brands understand about this market?
- What positioning opportunities exist?
```

**Template Variables:**
- `{count}` - Number of posts analyzed
- `{topic}` - Search query/topic
- `{corpus_summary}` - Bullet-pointed list of analysis snippets

---

## Step 5: Insight Extraction

**Purpose:** Extract strategic market intelligence from semiotic analyses using GPT-5-mini, organized by canonical sections.

### Section Insights Prompt

Applied to each of the 5 canonical sections (VISUAL CODES, CULTURAL MEANING, TABOO NAVIGATION, PLATFORM CONVENTIONS, CONSUMER PSYCHOLOGY).

```
You are analyzing the "{section_name}" insights from {doc_count} Xiaohongshu posts about {topic}.

# SAMPLE CONTENT FROM THIS SECTION:

{combined_content}

# TASK: Extract market intelligence

Analyze these {section_name} insights and provide:

## 1. BEHAVIORAL PATTERNS (150 words)
- What are consumers consistently doing and why?
- What needs or pain points keep appearing?
- Include specific examples from the data

## 2. MARKET DYNAMICS (100 words)
- What products/services are gaining traction?
- What purchase drivers and barriers exist?
- What pricing or value perceptions emerge?

## 3. CONSUMER SEGMENTS (100 words)
- What distinct consumer groups can you identify?
- How do their needs and behaviors differ?
- What motivates each segment?

## 4. STRATEGIC OPPORTUNITIES (150 words)
- What unmet needs represent market opportunities?
- What positioning would resonate?
- What should brands prioritize?

Return only the analysis in markdown format. Focus on actionable market insights.
```

**Template Variables:**
- `{section_name}` - One of the 5 canonical sections
- `{doc_count}` - Number of documents analyzed
- `{topic}` - Search query/topic
- `{combined_content}` - Sampled section text from up to 15 documents

**Configuration:**
- Max Output Tokens: `1200`
- Retry Max Tokens: `1800`

### Master Codebook Synthesis Prompt

Creates comprehensive strategic report from all section insights.

```
You are creating a strategic market report from insights about Xiaohongshu content on {topic}.

# SECTION INSIGHTS:

{insights_text}

# TASK: Create a comprehensive market analysis (600-700 words)

## 1. MARKET LANDSCAPE (150 words)
- What is the current state of this market?
- What products/services dominate and why?
- What trends are accelerating or declining?

## 2. CONSUMER SEGMENTATION (150 words)
- Who are the key consumer segments?
- What are their distinct needs and behaviors?
- How do they differ in values and purchasing power?

## 3. COMPETITIVE WHITE SPACE (150 words)
- What needs are underserved?
- Where do opportunities for differentiation exist?
- What positioning gaps can brands exploit?

## 4. STRATEGIC RECOMMENDATIONS (150-200 words)
- Top 5-7 strategic priorities for brands
- Specific market entry or expansion strategies
- Key success factors and potential barriers

Return the analysis in markdown format with clear, actionable insights for brand strategy.
```

**Template Variables:**
- `{topic}` - Search query/topic
- `{insights_text}` - Combined insights from all sections

---

## Step 6: Theme Enrichment

**Purpose:** Transform cluster analysis into detailed consumer segment profiles using GPT-5-mini.

### Theme Generation System Prompt

```
# IDENTITY and PURPOSE
You are an expert market research analyst with over 25 years experience in consumer segmentation and market opportunity analysis. You excel at identifying distinct consumer groups, their needs, and the market opportunities they represent. Your goal is to analyze clusters of consumer behavior to extract actionable market intelligence.

You are analyzing clusters from Xiaohongshu (Little Red Book) content to understand consumer segments and market dynamics.
```

### Theme Generation Prompt Template

```
# STEPS
- Analyze the cluster to identify the consumer segment it represents
- Define their core needs, behaviors, and values
- Identify market opportunities this segment presents
- Provide strategic recommendations for targeting this segment

# OUTPUT INSTRUCTIONS
- Only output Markdown
- Structure your response as follows:
  1. **Segment Name** (5-7 words describing this consumer group)
  2. **Core Identity** (one sentence defining who they are and what drives them)
  3. **Detailed Profile** (300-350 words covering):
     - Demographics and psychographics
     - Key behaviors and consumption patterns
     - Unmet needs and pain points
     - Purchase drivers and decision factors
     - Specific examples from the data
  4. **Market Opportunities** (3-4 specific opportunities)
  5. **Strategic Approach** (2-3 recommendations for engaging this segment)

# INPUT

INPUT:
{cluster_content}
```

**Template Variables:**
- `{cluster_content}` - Cluster ID, exemplar analysis, and sample analyses

**Configuration:**
- Max Output Tokens: `1500`
- Retry Max Tokens: `2000`

### Theme Synthesis Prompt

Creates overarching market analysis from all consumer segments.

```
You are synthesizing {theme_count} consumer segments from Xiaohongshu content analysis about {topic}.

# CONSUMER SEGMENTS IDENTIFIED:

{themes_text}

# TASK: Create a comprehensive market analysis (500-600 words) with this structure:

## 1. MARKET OVERVIEW (100 words)
- What does the segmentation reveal about this market?
- How mature is the market and where is it heading?

## 2. SEGMENT DYNAMICS (100 words)
- How do these segments interact and overlap?
- What are the size and growth potential of each?

## 3. COMPETITIVE LANDSCAPE (100 words)
- Which segments are over/underserved?
- Where are the opportunities for new entrants?

## 4. ECONOMIC IMPLICATIONS (100 words)
- What does this reveal about Chinese consumer spending?
- What are the pricing and value expectations?

## 5. GO-TO-MARKET STRATEGY (100-200 words)
- Priority segments and sequencing
- Key success factors for each segment
- Recommended positioning and messaging

Return only the final analysis text in markdown format. Focus on actionable insights.
```

**Template Variables:**
- `{theme_count}` - Number of cluster themes
- `{topic}` - Search query/topic
- `{themes_text}` - Combined theme analyses from all clusters

---

## Canonical Sections

The pipeline analyzes content across 5 standardized dimensions:

1. **VISUAL CODES** - Visual language, aesthetic patterns, design conventions
2. **CULTURAL MEANING** - Cultural values, symbolism, social context
3. **TABOO NAVIGATION** - How sensitive topics are addressed, boundaries navigated
4. **PLATFORM CONVENTIONS** - Xiaohongshu-specific posting patterns, engagement tactics
5. **CONSUMER PSYCHOLOGY** - Emotional drivers, motivations, decision-making patterns

These sections structure the analysis output in Step 2 and organize insights in Step 5.

---

## Report Templates

The pipeline includes 3 report templates (configured in `pipeline_config.json`):

### 1. SCQA Strategy Narrative
**Template:** `report_templates/scqa.md.jinja`

Deck-ready narrative following Situation-Complication-Question-Answer framework:
- Situation: Visual codes from the surface
- Complication: Cultural frictions and taboo navigation
- Question: Consumer psychology insights
- Answer: Strategic narrative from theme synthesis
- Activation Plays: From brand playbook
- Visual Evidence: Atlas and radar charts

### 2. Executive Decision Memo
**Template:** `report_templates/executive_memo.md.jinja`

C-level memo format:
- Executive Summary: Theme synthesis
- Market Signals: Cluster theme highlights
- Cultural Codes to Watch: Master codebook excerpt
- Activation Plan: Playbook bullets
- Next Steps: Metadata-driven follow-ups

### 3. LinkedIn Launch Brief
**Template:** `report_templates/linkedin_brief.md.jinja`

Social-ready content:
- Hook: Lead theme from enrichment
- Three Proof Points: Section highlights
- Call to Action: Social snippet from playbook
- Hero Visual: Semiotic atlas for posts

---

## Configuration Reference

All prompts are stored in `pipeline_config.json` under the `prompts` key:

```json
{
  "prompts": {
    "step2_semiotic_analysis": {
      "system_prompt": "...",
      "main_prompt": "...",
      "synthesis_prompt_template": "..."
    },
    "step5_insight_extraction": {
      "section_insights_prompt_template": "...",
      "master_codebook_prompt_template": "..."
    },
    "step6_theme_enrichment": {
      "theme_generation_system": "...",
      "theme_generation_prompt_template": "...",
      "synthesis_prompt_template": "..."
    }
  }
}
```

### API Configuration

```json
{
  "api_config": {
    "openai_model": "gpt-5-mini",
    "openai_max_output_tokens": 1200,
    "openai_retry_max_tokens": 1800,
    "openai_reasoning_effort": "medium",
    "openai_verbosity": "medium"
  }
}
```

### Accessing Prompts in Code

Use `config_loader.py`:

```python
from config_loader import get_config

config = get_config()

# Get a prompt
system_prompt = config.get_prompt('step2_semiotic_analysis', 'system_prompt')

# Get a prompt with template variables
synthesis_prompt = config.get_prompt(
    'step5_insight_extraction',
    'master_codebook_prompt_template',
    topic="coffee flavor",
    insights_text="..."
)
```

---

## Notes

- All prompts use markdown formatting for structured output
- Word counts are guidance; GPT-5-mini typically respects them closely
- Template variables use `{variable_name}` syntax
- Prompts emphasize **actionable market insights** over academic analysis
- Focus on **WHY** (motivations, strategies) over **WHAT** (descriptions)
- Chinese language references are encouraged when culturally relevant
- Rate limiting (2s delay) is applied between API calls to avoid throttling
