"""
TASK 3: Blueprint Engine — 3-Stage Claude API Pipeline
Blueprint Engine Orchestrator — Exsuvera LLC / LAB

Stage 1: Extraction — raw transcript → structured JSON
Stage 2: Enrichment — add scores, assessments, strategic recommendations
Stage 3: Generation — produce full branded business plan in Markdown
"""

import json
import os
import time
import logging
from typing import Optional

import anthropic

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Claude client
# ─────────────────────────────────────────────────────────────

def get_claude_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY environment variable is not set.")
    return anthropic.Anthropic(api_key=api_key)


def call_claude(client: anthropic.Anthropic, system_prompt: str,
                user_content: str, model: str = "claude-opus-4-5",
                max_tokens: int = 8000, retries: int = 1) -> str:
    """
    Call the Claude API with retry logic.
    Returns the text content of the response.
    """
    for attempt in range(retries + 1):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}]
            )
            return response.content[0].text
        except anthropic.APIError as e:
            logger.error(f"Claude API error (attempt {attempt + 1}): {e}")
            if attempt < retries:
                time.sleep(5)
            else:
                raise
        except Exception as e:
            logger.error(f"Unexpected error calling Claude (attempt {attempt + 1}): {e}")
            if attempt < retries:
                time.sleep(5)
            else:
                raise


# ─────────────────────────────────────────────────────────────
# Stage 1: Extraction
# ─────────────────────────────────────────────────────────────

STAGE1_SYSTEM = """You are the Blueprint Engine — Stage 1: Extraction Module.

You will receive a raw transcript from a Blueprint Session. Extract every relevant
data point and organize into structured JSON.

Extract into these categories:

- subject (name, email, phone, location, age, employment, education, experience,
  key_people, childhood_dream)
- business (name, pitch, problem, target_customer, why_it_must_exist, why_this_person,
  vision_12mo, vision_3yr, success_definition, legal_structure, ip)
- revenue_model (how_money_is_made, streams, pricing, rationale, expenses,
  current_revenue, capital, five_k_question_response)
- market (competitors, strengths, weaknesses, substitutes, differentiator, gap)
- operations (daily_routine, tools, marketing_channels, content_strategy,
  email_list, failed_marketing, priorities_90_day, biggest_obstacle,
  unlimited_resources_answer, partnerships)
- digital_presence (website, platform, satisfaction, social_profiles,
  best_platform, best_content_type, paid_ads_history, viral_posts, marketplaces,
  podcast_blog_newsletter, communities, feed_reflects_business)
- psychology (primary_fear, fear_consequences, avoidance_pattern, root_cause,
  hardest_feedback, feedback_impact, real_support_system,
  people_working_against_them, anything_unsaid)
- vault (other_ideas, recurring_idea, started_and_stopped, ai_tools_used,
  ai_use_cases, ai_barriers, tech_comfort, available_hours, workspace,
  internet, computer_vs_phone, smallest_action_this_week)
- thyself_lab_data (birthday, birth_time, birth_location)
- emotional_signals (excitement_moments, hesitation_moments, contradictions,
  energy_shifts, nervous_laughter_topics, post_interview_info)
- direct_quotes (most_revealing, strongest_vision, most_vulnerable, most_confident)

For any field not mentioned in the transcript, use null.
Output ONLY valid JSON. No markdown, no explanation, no preamble."""


def run_stage1_extraction(client: anthropic.Anthropic, transcript: str) -> dict:
    """Extract structured data from transcript using Claude."""
    logger.info("Stage 1: Extracting data from transcript...")
    raw = call_claude(
        client,
        system_prompt=STAGE1_SYSTEM,
        user_content=f"TRANSCRIPT:\n\n{transcript}",
        max_tokens=8000
    )
    # Strip any accidental markdown fences
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Stage 1 JSON parse error: {e}")
        logger.error(f"Raw output (first 500 chars): {raw[:500]}")
        # Return partial data with error flag
        return {"_parse_error": str(e), "_raw": raw[:2000]}


# ─────────────────────────────────────────────────────────────
# Stage 2: Enrichment
# ─────────────────────────────────────────────────────────────

STAGE2_SYSTEM = """You are the Blueprint Engine — Stage 2: Enrichment Module.

You will receive a JSON object containing:
- extracted_data: structured extraction from the Blueprint Session transcript
- social_audit: findings from the social media audit
- archetypal_profile: numerology and Human Design data (if available)

Analyze all data and produce a new JSON object with the following additions:

SCORES (each with numeric value 1-10 and rationale string):
- business_viability_score: { score, rationale, risks[], strengths[] }
- founder_readiness_score: { score, psychological, operational, financial, support }
- digital_maturity_score: { score, current_state, biggest_gap, best_platform, brand_alignment }
- ai_readiness_tier: { tier (0-4), label ("Unaware"/"Curious"/"Experimenter"/"Integrator"/"Builder"), description }
- identity_coherence: { stated_vision, actual_behavior, alignment_score (1-10), primary_misalignment, correction }
- revenue_model_assessment: { type, sustainability, diversification, recommended_additions[], path_to_1k, path_to_10k }

STRATEGIC RECOMMENDATIONS:
- primary_business_model_recommendation
- pricing_adjustment
- target_market_refinement
- competitive_positioning_statement
- content_strategy_recommendation
- first_7_days: []
- first_30_days: []
- first_90_days: []
- tools_to_adopt: []
- partnerships_to_pursue: []
- revenue_quick_wins: []
- long_term_moat

PLAN CALIBRATION:
- aggressiveness_level: "Conservative" | "Moderate" | "Assertive" | "Aggressive"
  (based on founder_readiness_score: <4=Conservative, 4-6=Moderate, 7-8=Assertive, 9-10=Aggressive)
- implementation_speed
- tone_of_plan
- areas_requiring_sensitivity: []
- motivational_framing

CRITICAL: Incorporate the social media audit data. The digital_maturity_score
and content_strategy_recommendation MUST reflect ACTUAL profile data, not
just what the subject told you. Flag any gaps between stated intentions and
observed digital behavior.

Output ONLY valid JSON. No markdown, no explanation, no preamble."""


def run_stage2_enrichment(client: anthropic.Anthropic, stage1_data: dict,
                          social_audit: dict, archetypal_profile: dict) -> dict:
    """Enrich extracted data with strategic assessments using Claude."""
    logger.info("Stage 2: Enriching data with strategic assessments...")
    merged = {
        "extracted_data": stage1_data,
        "social_audit": social_audit,
        "archetypal_profile": archetypal_profile
    }
    user_content = json.dumps(merged, ensure_ascii=False, indent=2)
    raw = call_claude(
        client,
        system_prompt=STAGE2_SYSTEM,
        user_content=user_content,
        max_tokens=8000
    )
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Stage 2 JSON parse error: {e}")
        return {"_parse_error": str(e), "_raw": raw[:2000]}


# ─────────────────────────────────────────────────────────────
# Stage 3: Generation
# ─────────────────────────────────────────────────────────────

STAGE3_SYSTEM_PASS1 = """You are the Blueprint Engine — Stage 3: Generation Module.

Generate a COMPLETE, PROFESSIONAL, PERSONALIZED business plan as a gift
from Lion Ass Bitch (LAB) / Exsuvera LLC.

RULES:
1. Write in second person ("you" / "your")
2. Reference specific things they said — use their exact words in quotes
3. Do not sugarcoat weaknesses — name them clearly, then provide a path through
4. Every recommendation ties to specific interview data
5. Implementation starts from THEIR stated smallest action
6. Archetypal data woven naturally if available
7. Respect plan_calibration parameters
8. Social media audit findings integrated into Digital Positioning section
   with real data, not assumptions

Generate ONLY these sections (Pass 1 of 2):

# I. EXECUTIVE SUMMARY
# II. FOUNDER PROFILE
# III. COMPANY DESCRIPTION
# IV. MARKET ANALYSIS
# V. COMPETITIVE ANALYSIS
# VI. PRODUCTS & SERVICES
# VII. REVENUE MODEL & FINANCIAL OVERVIEW
# VIII. MARKETING & CUSTOMER ACQUISITION STRATEGY

Write in clean Markdown. Be thorough, specific, and personal.
Each section should be substantive — minimum 300 words per section.
Use the subject's actual words and specific details from the transcript."""

STAGE3_SYSTEM_PASS2 = """You are the Blueprint Engine — Stage 3: Generation Module (Pass 2).

Continue generating the business plan. You are writing the SECOND HALF.

RULES:
1. Write in second person ("you" / "your")
2. Reference specific things they said — use their exact words in quotes
3. Do not sugarcoat weaknesses — name them clearly, then provide a path through
4. Every recommendation ties to specific interview data
5. Implementation starts from THEIR stated smallest action
6. Archetypal data woven naturally if available
7. Respect plan_calibration parameters
8. Social media audit findings integrated into Digital Positioning section

Generate ONLY these sections (Pass 2 of 2):

# IX. DIGITAL POSITIONING REPORT
*(Powered by real social audit data — include actual metrics, platform assessments,
gap analysis, and specific recommendations based on observed profile data)*

# X. OPERATIONS PLAN

# XI. ARCHETYPAL ALIGNMENT REPORT
*(Only if archetypal data was available — weave Life Path and Human Design naturally)*

# XII. IMPLEMENTATION ROADMAP
## Week 1: The Spark
*(Start with their stated smallest action)*
## Days 8–30: The Foundation
## Days 31–90: The Build
## Months 4–12: The Scale

# XIII. RISK ASSESSMENT & CONTINGENCY

# XIV. FOUNDER LETTER
*(Personal, warm, direct. Reference the most powerful thing they said.
Tell them what the plan sees in them. End with a call to action to BEGIN, not to buy.)*

---
*Engineered with precision. Delivered with purpose.*
*— The Blueprint Session, Exsuvera LLC*

Write in clean Markdown. Be thorough, specific, and personal."""


def run_stage3_generation(client: anthropic.Anthropic, stage1_data: dict,
                          stage2_data: dict, social_audit: dict,
                          archetypal_profile: dict) -> str:
    """Generate the full business plan in Markdown using two Claude passes."""
    logger.info("Stage 3: Generating business plan (Pass 1)...")

    enriched_context = json.dumps({
        "extracted_data": stage1_data,
        "enrichment": stage2_data,
        "social_audit": social_audit,
        "archetypal_profile": archetypal_profile
    }, ensure_ascii=False, indent=2)

    # Pass 1: Sections I–VIII
    pass1 = call_claude(
        client,
        system_prompt=STAGE3_SYSTEM_PASS1,
        user_content=enriched_context,
        max_tokens=8000
    )
    logger.info("Stage 3: Generating business plan (Pass 2)...")

    # Pass 2: Sections IX–XIV
    pass2 = call_claude(
        client,
        system_prompt=STAGE3_SYSTEM_PASS2,
        user_content=enriched_context,
        max_tokens=8000
    )

    # Concatenate
    full_plan = pass1.strip() + "\n\n---\n\n" + pass2.strip()
    return full_plan


# ─────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────

def run_blueprint_engine(transcript: str, social_audit: dict,
                         archetypal_profile: dict,
                         output_dir: str = "/home/ubuntu/blueprint_engine/output") -> dict:
    """
    Execute the full 3-stage Blueprint Engine pipeline.

    Returns:
        dict with stage1_json, stage2_json, business_plan_markdown
    """
    client = get_claude_client()
    os.makedirs(output_dir, exist_ok=True)

    # Stage 1
    stage1_data = run_stage1_extraction(client, transcript)
    stage1_path = os.path.join(output_dir, "stage1_extraction.json")
    with open(stage1_path, "w") as f:
        json.dump(stage1_data, f, indent=2)
    logger.info(f"Stage 1 saved: {stage1_path}")

    # Stage 2
    stage2_raw = run_stage2_enrichment(client, stage1_data, social_audit, archetypal_profile)
    # Normalize: if Claude nested scores under a 'scores' key, flatten for consistency
    stage2_data = stage2_raw
    stage2_path = os.path.join(output_dir, "stage2_enrichment.json")
    with open(stage2_path, "w") as f:
        json.dump(stage2_data, f, indent=2)
    logger.info(f"Stage 2 saved: {stage2_path}")

    # Stage 3
    business_plan_md = run_stage3_generation(
        client, stage1_data, stage2_data, social_audit, archetypal_profile
    )
    plan_path = os.path.join(output_dir, "business_plan.md")
    with open(plan_path, "w") as f:
        f.write(business_plan_md)
    logger.info(f"Business plan saved: {plan_path}")

    return {
        "stage1_data": stage1_data,
        "stage2_data": stage2_data,
        "business_plan_markdown": business_plan_md,
        "stage1_path": stage1_path,
        "stage2_path": stage2_path,
        "plan_path": plan_path
    }
