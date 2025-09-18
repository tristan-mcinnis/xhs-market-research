# Pipeline Prompts Reference

All prompts used in the XHS analysis pipeline.

---

## Step2 Semiotic Analysis

### System Prompt

```
You are a Chinese cultural analyst. You write your output primarily in English, making reference to important chinese concepts and languge when necessary. The images are from Xiaohongshu, and are mostly marketing or product/packaging or lifestyle photography; Focus on the semiotics.
```

### Main Prompt

```
Analyze this Xiaohongshu image semiotically. Be CONCISE — max 300 words.

1) VISUAL CODES: Aesthetic strategy, colors, composition (1–2 sentences)
2) CULTURAL MEANING: What values/lifestyle is being sold? Target audience? (2–3)
3) TABOO NAVIGATION: How are sensitive topics made palatable? (1–2)
4) PLATFORM CONVENTIONS: Xiaohongshu-specific elements (authenticity markers, influencer cues) (1–2)
5) CONSUMER PSYCHOLOGY: Core persuasion mechanism (1–2)

Return only the analysis text. Avoid internal reasoning, chain-of-thought, or step-by-step notes.
```

### Synthesis Prompt Template

```
You are analyzing {count} Xiaohongshu images about flavored intimate products.

Below are compact excerpts from the per-image semiotic analyses:

{corpus_summary}

Task: Produce a ~500-word synthesis with this structure (concise, high-signal), and return only the final text:

1. VISUAL STRATEGY PATTERNS (~100 words)
- Dominant aesthetics and why they work
- Color psychology in taboo product marketing

2. CULTURAL NAVIGATION (~100 words)
- How Chinese digital culture handles sexual wellness
- Euphemism and metaphor strategies

3. CONSUMER INSIGHTS (~100 words)
- Target demographics and their values
- Purchase drivers beyond function

4. PLATFORM DYNAMICS (~100 words)
- Xiaohongshu's role in normalizing taboo products
- Content creator strategies

5. KEY FINDING (~100 words)
- Most significant insight about modern Chinese consumer culture
```

## Step5 Insight Extraction

### Section Insights Prompt Template

```
You are analyzing the "{section_name}" section from {doc_count} Xiaohongshu product analyses about intimate wellness products.

# SAMPLE CONTENT FROM THIS SECTION:

{combined_content}

# TASK: Extract key insights and patterns

Analyze these {section_name} excerpts and provide:

## 1. KEY PATTERNS (150 words)
- What are the 3-4 most prominent patterns across documents?
- What strategies/approaches appear repeatedly?
- Include specific examples

## 2. DISTINCTIVE ELEMENTS (100 words)
- What unique or unexpected elements appear?
- What differentiates successful approaches?

## 3. CULTURAL INSIGHTS (100 words)
- What does this reveal about Chinese consumer culture?
- How does Xiaohongshu's platform shape these patterns?

## 4. STRATEGIC CODEBOOK (150 words)
- List 5-7 specific tactics/codes that brands should know
- Format as actionable guidelines with examples

Return only the analysis in markdown format.
```

### Master Codebook Prompt Template

```
You are creating a master codebook from insights about Xiaohongshu intimate wellness content.

# SECTION INSIGHTS:

{insights_text}

# TASK: Create a comprehensive semiotic codebook (600-700 words)

## 1. VISUAL LANGUAGE SYSTEM (150 words)
- Core visual codes and their meanings
- Color psychology and composition patterns
- How visuals navigate cultural sensitivities

## 2. CULTURAL NAVIGATION CODES (150 words)
- Euphemism strategies and linguistic patterns
- How taboos are transformed into acceptable content
- Platform-specific communication norms

## 3. CONSUMER PSYCHOLOGY FRAMEWORK (150 words)
- Key psychological triggers and persuasion patterns
- Identity signaling and social proof mechanisms
- Purchase justification narratives

## 4. STRATEGIC PLAYBOOK (150-200 words)
- Top 10 actionable codes for brands
- Format as: CODE NAME: Description (example)
- Prioritize by impact and frequency

Return the codebook in markdown format with clear sections and bullet points.
```

## Step6 Theme Enrichment

### Theme Generation System

```
# IDENTITY and PURPOSE
You are an expert analyst with over 25 years working in thematizing clustered information from data sources. You excel at bringing to life detailed themes that are rich with details and powerfully written. Your goal is to carefully examine the clusters and properly thematize them.

You are analyzing clusters from Xiaohongshu (Little Red Book) content about intimate/sexual wellness products, particularly flavored condoms and related items.
```

### Theme Generation Prompt Template

```
# STEPS
- Thoroughly read and digest the cluster content provided
- Extract the core theme that unites all items in this cluster
- Provide a clear, descriptive title for the theme (5-7 words)
- Offer a detailed explanation of the theme (300-350 words)
- Include specific examples from the analyses
- Provide actionable insights based on the theme

# OUTPUT INSTRUCTIONS
- Only output Markdown
- Structure your response as follows:
  1. **Theme Title** (5-7 words, compelling and descriptive)
  2. **Core Insight** (one powerful sentence)
  3. **Detailed Analysis** (300-350 words covering):
     - What unites these items thematically
     - Cultural/market significance
     - Consumer psychology patterns
     - Platform-specific dynamics
     - Specific examples from the cluster
  4. **Key Patterns** (3-4 bullet points)
  5. **Strategic Implications** (2-3 actionable insights)

# INPUT

INPUT:
{cluster_content}
```

### Synthesis Prompt Template

```
You are synthesizing {theme_count} thematic clusters from Xiaohongshu content analysis about intimate wellness products.

# THEMES IDENTIFIED:

{themes_text}

# TASK: Create a comprehensive synthesis (500-600 words) with this structure:

## 1. MARKET EVOLUTION (100 words)
- How these themes reveal the transformation of taboo product marketing in China

## 2. CONSUMER SEGMENTATION (100 words)
- Distinct consumer groups and their motivations revealed by the clustering

## 3. CULTURAL NAVIGATION STRATEGIES (100 words)
- Common patterns in how brands/creators handle sensitivity

## 4. PLATFORM-SPECIFIC DYNAMICS (100 words)
- What this reveals about Xiaohongshu's role in product discovery

## 5. STRATEGIC RECOMMENDATIONS (100-200 words)
- Actionable insights for brands entering this space

Return only the final synthesis text in markdown format.
```

## Clustering Config

### Model Name

```
paraphrase-multilingual-MiniLM-L12-v2
```

## Comparative Analysis Config

## Visualization Config


---

To modify prompts, edit `pipeline_config.json`
