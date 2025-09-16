# Stanford Medical Template Generation - Public Release

This repository contains the key prompts and examples from our research on automated medical template generation for e-consult systems.

## Contents

1. **Prioritizer Agent Prompt** - The prompt used to rank template components by clinical importance
2. **Final Evaluator Prompt (v8)** - The evaluation prompt used to assess generated templates
3. **DSPy Optimization Artifact** - Example of the optimized prompting structure created by DSPy

## Files

- `prioritizer_prompt.py` - The prioritization agent that ranks template components
- `evaluator_prompt_v8.py` - The final evaluation prompt used in our experiments
- `dspy_optimization_example.json` - Example DSPy optimization artifact with learned prompts and examples
- `dspy_full_prompt_exact.txt` - The EXACT prompt passed to the model when generating templates (no placeholders or summaries)

## Background

These prompts were used in our research on automated medical template generation for specialist e-consult systems. The prioritizer agent helps rank template components by clinical importance, while the evaluator assesses generated templates for comprehensiveness and clinical utility.

The DSPy optimization process learned to generate medical templates that balance comprehensiveness with conciseness, using few-shot examples and optimized instructions.

## Citation

If you use these prompts in your research, please cite our paper:

[Citation information to be added]