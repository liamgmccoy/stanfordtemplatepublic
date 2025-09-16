"""
Prioritization Prompt v1: Clinical Importance Ranking

Ranks template components by clinical importance for the given specialty and condition.
Focuses on identifying which assessments and diagnostics are most critical for
clinical decision-making in e-consult contexts.

The goal is to help rank components so that only the top-N most important ones
are included in the final template, addressing verbosity while maintaining
clinical comprehensiveness.
"""

import json
import re

def generate_prioritization_prompt(template_components: list, specialty: str, condition: str):
    """Generate prompt to rank template components by clinical importance"""

    # Format components for ranking
    components_text = ""
    for i, component in enumerate(template_components, 1):
        components_text += f"{i}. {component}\n"

    prompt = f"""You are a clinical expert in {specialty} evaluating an e-consult template for {condition}.

Your task is to rank the following template components in order of CLINICAL IMPORTANCE for making diagnostic and treatment decisions in an e-consult setting.

CONTEXT:
- This is for e-consult triage and specialist recommendations
- Primary care providers will use this template to gather information
- The specialist will make recommendations based on this information
- Some components may be cut from the final template due to length constraints

COMPONENTS TO RANK:
{components_text}

RANKING CRITERIA (in order of importance):
1. **Critical for Diagnosis**: Information essential for making a differential diagnosis
2. **Treatment Decision Impact**: Data that directly influences treatment recommendations
3. **Risk Stratification**: Information needed to assess urgency/severity
4. **Standard of Care**: Components typically required in specialist evaluation
5. **Additional Context**: Helpful but not essential supplementary information

INSTRUCTIONS:
1. Rank ALL components from 1 (most important) to {len(template_components)} (least important)
2. For each ranking, provide a brief clinical justification
3. Consider what information is absolutely essential vs. "nice to have"
4. Think about what a specialist MUST know vs. what they'd LIKE to know

OUTPUT FORMAT:
Provide your ranking as a JSON object with this structure:
{{
    "rankings": [
        {{
            "rank": 1,
            "component": "exact component text here",
            "justification": "clinical reasoning for this ranking"
        }},
        ...
    ],
    "summary": {{
        "critical_threshold": "rank where components become non-essential (e.g., 8)",
        "reasoning": "brief explanation of your ranking strategy"
    }}
}}

Begin your clinical importance ranking:"""

    return prompt

def parse_ranking_response(response: str) -> dict:
    """Parse the LLM ranking response into structured data"""
    try:
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            ranking_data = json.loads(json_match.group())
            return ranking_data
        else:
            # Fallback parsing if JSON extraction fails
            return {"error": "Failed to parse ranking response", "raw_response": response}
    except json.JSONDecodeError as e:
        return {"error": f"JSON decode error: {str(e)}", "raw_response": response}
    except Exception as e:
        return {"error": f"Parsing error: {str(e)}", "raw_response": response}