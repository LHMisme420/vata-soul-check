---
title: VATA - Code Soul Scanner & Humanizer
emoji: 🧬
colorFrom: indigo
colorTo: blue
sdk: gradio
sdk_version: 4.0.0
app_file: app.py
pinned: false
license: mit
---
# VATA — Code Soul Scanner & Humanizer

**VATA** is a hybrid analysis engine that evaluates code for human authenticity, style signals, risk patterns, and structural intent.  
It blends:

- Forensic scoring  
- Explainable metrics  
- Rule‑based humanization  
- Optional Grok LLM refinement  

…to produce a final output that feels natural, readable, and grounded in real engineering patterns.

---

## What VATA Does

### 1. Soul Score Analysis
Your code is evaluated across multiple dimensions:

- Comment quality and density  
- Naming clarity and variance  
- Structural complexity  
- Repetition and duplication  
- Line‑length variance  
- Risky patterns (eval, exec, subprocess, secrets, etc.)  
- Language‑specific signals  

You receive:

- Soul Score (0–100%)  
- Energy classification  
- Human vs machine probability  
- VATA verdict  
- Tier rating  
- Full metric breakdown  

---

### 2. Rule‑Based Humanizer
This pass adds subtle, realistic human touches:

- Natural comments  
- Debug traces  
- Minor inconsistencies  
- Occasional redundancy  
- Optional sarcasm  
- Optional naming flair  
- Style presets (Casual, Professional, Sarcastic, Minimal)

Everything is deterministic and explainable — no hallucinations, no logic changes.

---

### 3. Grok LLM Blending (Optional)
If you provide an **XAI Grok API key**, VATA sends the humanized code to Grok for a final polish:

- More natural comments  
- Cleaner flow  
- Slightly improved readability  
- Preserved logic  
- No structural rewrites  

If no API key is provided, VATA simply skips this step.

---

## How to Use

1. Paste your code into the left panel.  
2. (Optional) Enter your Grok API key.  
3. Adjust humanizer settings if desired.  
4. Click **Run VATA Pipeline**.  
5. Read the results on the right:

- Soul Score  
- Breakdown  
- Humanized code  
- Grok‑blended code (if enabled)

---

## Why VATA Exists

Modern code is increasingly machine‑generated.  
Teams need tools that:

- Detect AI‑generated patterns  
- Evaluate code quality signals  
- Provide explainable metrics  
- Humanize machine‑written code  
- Improve readability without rewriting logic  

VATA fills that gap with a transparent, explainable, and developer‑friendly approach.

---

## What VATA Does Not Do

- It does not rewrite logic.  
- It does not optimize algorithms.  
- It does not guarantee authorship attribution.  
- It does not store or transmit your code (unless you choose to use Grok).  

---

## Roadmap

Planned enhancements:

- Multi‑language expansion (Go, Rust, Swift, PHP)  
- Drift detection between original → humanized → blended  
- Persona presets (Senior Engineer, Intern, Legacy Wizard, etc.)  
- Side‑by‑side diff viewer  
- Export options  
- VATA lineage fingerprinting  