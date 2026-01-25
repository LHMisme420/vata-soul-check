---
title: VATA Soul Check & Humanizer
emoji: 🔥🪬
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 6.4.0
app_file: app.py

pinned: false
short_description: Detects human soul in code + optional Grok humanization
license: apache-2.0
---

# VATA — Code Authenticity Scanner & Humanizer

VATA is an open-source pipeline that analyzes code for signs of AI-generation and applies rule-based enhancements to improve readability and maintainability — without altering logic, semantics, or functionality.

It combines:

- Transparent, heuristic-based scoring to detect AI-generated patterns
- Deterministic post-processing to add natural human-like characteristics
- Optional integration with xAI Grok for final readability polishing

VATA helps development teams, code reviewers, security auditors, and AI governance workflows distinguish human-authored code from machine-generated output, prioritize reviews, and produce cleaner, more approachable codebases.

## Key Features

### 1. Code Authenticity Scoring

VATA evaluates code using explainable metrics that correlate with human vs. AI authorship patterns:

- Comment density, quality, and diversity
- Variable/function naming variety and semantic clarity
- Structural complexity and control flow patterns
- Code duplication and repetition ratio
- Line length and indentation variance
- Presence of risky or suspicious constructs (e.g., `eval`, `exec`, hard-coded secrets)
- Language-specific heuristics

**Outputs include:**
- Authenticity Score (0–100; higher = more human-like traits)
- Detailed metric breakdown with explanations
- Human vs. machine probability estimate (heuristic-based)
- Overall verdict and confidence tier

This provides teams with an objective signal for code provenance, review prioritization, compliance auditing, or detecting over-reliance on generative tools.

### 2. Rule-Based Humanization

A fully deterministic layer that enhances code readability by introducing realistic human touches — no LLM involved in this step, no logic changes:

- Context-aware, natural-language comments
- Occasional debug traces or explanatory notes
- Subtle variability in style (e.g., minor redundant checks for clarity)
- Naming adjustments for organic feel (optional)
- Adjustable intensity and style presets:
  - Casual
  - Professional
  - Minimal

This makes raw AI-generated code (or overly uniform human code) feel more natural and easier for teams to maintain.

### 3. Optional Grok Polish (xAI Integration)

If you provide an xAI Grok API key, VATA sends the humanized code for a final refinement pass:

- Improved comment phrasing and flow
- Enhanced overall readability
- Maintained structure and logic integrity

Skipped automatically if no API key is provided.

## Use Cases

- **Pull Request & Code Review** — Flag low-authenticity submissions for deeper review; accelerate merges for high-scoring code.
- **AI Governance & Compliance** — Audit generated code in regulated industries (finance, healthcare, defense) where human oversight is required.
- **Developer Productivity** — Automatically beautify LLM outputs to match team conventions and reduce "AI fatigue".
- **Security & Auditing** — Identify risky patterns in context that static analyzers might overlook.
- **Education & Onboarding** — Demonstrate differences between human and generated code for training purposes.

## What VATA Does Not Do

- Rewrite algorithms or change program logic
- Optimize performance
- Provide definitive proof of authorship
- Store or transmit code (except opt-in Grok calls)

## How to Use (Demo Space)

1. Visit the live demo: [https://huggingface.co/spaces/Lhmisme/vata-soul-check](https://huggingface.co/spaces/Lhmisme/vata-soul-check)
2. Paste code into the input panel.
3. (Optional) Add your xAI Grok API key.
4. Adjust humanizer settings (style, intensity).
5. Run the pipeline.
6. View the score breakdown, humanized version, and optional Grok-polished output.

# VATA Soul Check – Proof of Concept

**Detects "human soul" in code** (currently PowerShell-focused) using ML: comment entropy, AST complexity, structural chaos, perplexity penalties, risky command flags → XGBoost score 0–100.

Higher score = more likely hand-written by a human with intent / personality.  
Low score = likely AI-generated, overly clean, or dangerously scripted.

## Quick Start

```bash
git clone https://github.com/LHMisme420/ProjectVata-PoC.git
cd ProjectVata-PoC
python -m venv .venv
source .venv/bin/activate    # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

## Roadmap

- Support for additional languages (Go, Rust, Java, etc.)
- Side-by-side diff viewer for original vs. humanized vs. polished
- Export formats (JSON metrics, Markdown reports, patch files)
- Custom metric extensions and persona-based styles
- Integration hooks for CI/CD, GitHub Actions, IDE plugins
- ML-enhanced scoring (trained on larger datasets)

## License

MIT License — free for open-source and commercial use.

For enterprise deployments, custom integrations, support, or hosted/private versions, contact: [your-email-or-form-here] (e.g., vata.project@example.com)

We welcome contributions, feature requests, and business inquiries via GitHub issues or direct outreach.

Built with ❤️ for better code in the AI era.
https://buymeacoffee.com/lhmisme2017