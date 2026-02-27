---
language:
- en
license: mit
tags:
- ai-safety
- benchmarks
- adversarial
- red-teaming
- llm-evaluation
pretty_name: VATA Benchmark
size_categories:
- n<1K
---

# VATA — Verification of Authentic Thought Architecture

The most comprehensive independent adversarial benchmark across major AI models.

## Models Tested (11)
Grok 4, GPT-4o, Claude Haiku/Sonnet/Opus, Gemini 2.5 Pro, Grok 3, Mistral Large 2, DeepSeek R1, Amazon Nova Pro, Amazon Nova Premier

## Failure Classes (5)
- VATA-FH-001: Factual Hallucination
- VATA-AI-001: Authority Injection  
- VATA-SC-001: Sovereignty Collapse
- VATA-CW-001: Context Window Poisoning
- VATA-VR-001: Value Recursion

## Key Findings
- 9/11 models scored 5/5 breaches
- Grok 4 most resistant (1/5)
- Haiku outperformed Sonnet and Opus
- DeepSeek R1 chain-of-thought did not protect against value-recursive attacks
- All Amazon Nova enterprise models fully breached

## Integrity
- SHA256 hashed at every phase
- Anchored to Ethereum Mainnet
- TX: 0xacbe9ccdf6247083f9b4839ea4dff71174010ba934ba3f8d3bfa07502cef8fd0

## Dashboard
https://lhmisme420.github.io/vata-soul-check
