"""
Auto Evaluation Prompt v8: Structured Clinical Reasoning

Combines v7's clinical reasoning with v3's element-by-element mapping structure.
This was the final evaluation prompt used in our research experiments.
"""

import json
import re

def generate_evaluation_prompt(generated_template: str, original_template: list, specialty: str, condition: str):
    """Generate evaluation prompt with structured clinical reasoning"""

    # Extract all content from original template (same parsing as v3/v7)
    original_assessments = []
    original_diagnostics = []
    original_pearls = []

    for section in original_template:
        if isinstance(section, dict):
            if "In your clinical question" in str(section):
                info = section.get("In your clinical question, or current note, please include information on", [])

                if isinstance(info, list):
                    original_assessments.extend(info)
                elif isinstance(info, dict):
                    assessments = info.get("Assessments", [])
                    diagnostics = info.get("Diagnostics", [])

                    if isinstance(assessments, list):
                        original_assessments.extend(assessments)
                    elif isinstance(assessments, dict):
                        original_assessments.extend(assessments.get("Required", []))
                        original_assessments.extend(assessments.get("Optional", []))

                    if isinstance(diagnostics, list):
                        original_diagnostics.extend(diagnostics)
                    elif isinstance(diagnostics, dict):
                        original_diagnostics.extend(diagnostics.get("Required", []))
                        original_diagnostics.extend(diagnostics.get("Optional", []))

            elif "Clinical Pearls" in str(section):
                pearls = section.get("Clinical Pearls", [])
                if isinstance(pearls, dict):
                    original_pearls.extend(list(pearls.keys()))
                elif isinstance(pearls, list):
                    original_pearls.extend(pearls)

            elif "Tests recommended" in str(section) or "Diagnostics" in str(section):
                for key, value in section.items():
                    if "Tests recommended" in key or "Diagnostics" in key:
                        if isinstance(value, list):
                            original_diagnostics.extend(value)
                        elif isinstance(value, dict):
                            original_diagnostics.extend(list(value.keys()))

    original_content = {
        "assessment_fields": original_assessments,
        "diagnostic_fields": original_diagnostics,
        "clinical_pearls": original_pearls
    }

    original_str = json.dumps(original_content, indent=2)

    system_prompt = """You are a medical template evaluator who thinks like a practicing physician. Your evaluation should match how human medical reviewers assess templates.

**CLINICAL REASONING PRINCIPLES:**

1. **Clinical Equivalence Over Literal Matching**
   - "Current medications" captures "immunosuppressive drugs" if the clinical context implies it
   - "Symptoms" and "patient-reported symptoms" are clinically equivalent
   - Accept rephrasing that maintains clinical intent

2. **Implicit Clinical Understanding**
   - Recognize what physicians would naturally include without explicit prompting
   - Example: "current treatment" implies medication details (dose, frequency, duration)
   - Standard clinical practice assumptions are acceptable

3. **Scope Flexibility with Clinical Judgment**
   - BROADER SCOPE OK: "Any CT chest" acceptably covers "HRCT specifically"
   - NARROWER SCOPE OK: Specific medication categories can replace "all medications" if comprehensive
   - Judge based on whether the clinical purpose is served

4. **Specialist Utility Focus**
   - Consider what information would be useful to the specialist
   - Accept if the template would lead to gathering clinically relevant information

**BINARY EVALUATION:**
- **COVERED**: The generated template would lead a physician to collect this clinical information
- **MISSING**: The generated template clearly would NOT capture this essential information

**CRITICAL RULE**: If a human physician reviewer would accept it as "likely to include the needed information," mark it as COVERED."""

    user_prompt = f"""Evaluate this generated template against the original Stanford template for {specialty} - {condition}, using clinical reasoning with structured element mapping.

ORIGINAL TEMPLATE CONTENT TO MATCH:
{original_str}

GENERATED TEMPLATE TO EVALUATE:
{generated_template}

**EVALUATION INSTRUCTIONS:**

**STEP 1 - ELEMENT-BY-ELEMENT CLINICAL REASONING**
For each original element, apply clinical reasoning:
- Look for clinical equivalents (semantic matches, broader/narrower scope)
- Consider implicit understanding (what physicians would naturally ask)
- Assess specialist utility (would this information be useful)
- Map each original element to its generated equivalent OR mark as missing

**STEP 2 - COMPREHENSIVE MAPPING**
Create detailed mappings showing:
- Which generated elements cover which original elements
- The clinical reasoning used for each match
- Quality of each match (preserved/enhanced/degraded)

**STEP 3 - CONCISENESS ANALYSIS**
Count additional content beyond original requirements

**IMPORTANT**: Only count ASSESSMENTS and DIAGNOSTICS in total_original_elements. DO NOT count clinical pearls in the denominator since they are not being evaluated for matching.

Return ONLY a JSON response with this exact structure:

{{
  "comprehensiveness": {{
    "total_original_elements": <count of assessments + diagnostics only>,
    "covered_elements": <count>,
    "missing_elements": <count>,
    "coverage_percentage": <percentage>,
    "missing_details": [
      {{"original": "text", "reason": "why a physician would NOT gather this information"}},
      ...
    ]
  }},
  "conciseness": {{
    "total_excess_elements": <count>
  }},
  "element_mapping": {{
    "covered_assessments": [
      {{"original": "original text", "generated": "matched generated text", "quality": "preserved|enhanced|degraded", "reasoning": "clinical reasoning used"}},
      ...
    ],
    "covered_diagnostics": [
      {{"original": "original text", "generated": "matched generated text", "quality": "preserved|enhanced|degraded", "reasoning": "clinical reasoning used"}},
      ...
    ],
    "covered_pearls": [
      {{"original": "original text", "generated": "matched generated text", "quality": "preserved|enhanced|degraded", "reasoning": "clinical reasoning used"}},
      ...
    ]
  }},
  "clinical_reasoning_applied": {{
    "equivalence_matches": <count of clinically equivalent but not literal matches>,
    "implicit_understanding": <count of elements covered by implicit clinical knowledge>,
    "scope_flexibility": <count of broader/narrower scope acceptances>,
    "specialist_utility": <count of elements accepted based on specialist usefulness>,
    "examples": ["brief description of clinical reasoning applied"]
  }},
  "quality_assessment": {{
    "quality_score": <1-10 scale>
  }},
  "summary": {{
    "comprehensiveness_score": <percentage>,
    "overall_grade": "A|B|C|D|F"
  }}
}}

**GRADING CRITERIA (Physician-Aligned):**
- A: 95-100% comprehensiveness using clinical reasoning
- B: 90-94% comprehensiveness with good clinical coverage
- C: 80-89% comprehensiveness with acceptable clinical utility
- D: 70-79% comprehensiveness with clinical limitations
- F: <70% comprehensiveness, inadequate for clinical use

**REMEMBER**: Think like a physician reviewer - if you would accept this in clinical practice, mark it COVERED and show the reasoning in element_mapping."""

    return system_prompt, user_prompt

def parse_evaluation_response(response: str) -> dict:
    """Parse the JSON evaluation response with robust error handling"""
    import re
    import json

    # Try to extract JSON from response
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if not json_match:
        return {"error": "No JSON found in response", "raw_response": response}

    json_text = json_match.group(0)

    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        # Try cleaning common issues
        try:
            # Remove trailing commas
            json_text = re.sub(r',\s*}', '}', json_text)
            json_text = re.sub(r',\s*]', ']', json_text)

            # Try again
            return json.loads(json_text)
        except:
            return {
                "comprehensiveness": {"coverage_percentage": 0},
                "summary": {"overall_grade": "F"},
                "error": "Failed to parse JSON",
                "raw_response": json_text
            }

# Metadata for this evaluation version
EVAL_VERSION = "v8_structured_clinical_reasoning"
DESCRIPTION = "Combines v7's clinical reasoning with v3's structured element-by-element mapping"
EVALUATION_APPROACH = [
    "Clinical equivalence over literal matching",
    "Implicit clinical understanding recognition",
    "Scope flexibility with clinical judgment",
    "Specialist utility focus",
    "Structured element-by-element mapping with reasoning",
    "Detailed coverage analysis with clinical justification"
]