"""
TASK 2: Archetypal Profiling Module
Blueprint Engine Orchestrator — Exsuvera LLC / LAB

Calculates Life Path Number (Numerology) and Human Design Type
from birthday, birth time, and birth location.
"""

import json
import logging
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Numerology: Life Path Number
# ─────────────────────────────────────────────────────────────

MASTER_NUMBERS = {11, 22, 33}

LIFE_PATH_PROFILES = {
    1: {
        "title": "The Leader",
        "leadership_style": (
            "Life Path 1s are natural pioneers. In business, they lead from the front — "
            "they are most effective when they own their vision completely and resist the "
            "urge to seek consensus before acting. They thrive as the face of their brand."
        ),
        "business_strengths": (
            "Independent thinking, bold decision-making, original ideas, the ability to "
            "start things from scratch, and an innate drive that others find magnetic."
        ),
        "blindspots": (
            "Stubbornness, difficulty delegating, and a tendency to burn out from trying "
            "to do everything alone. Can struggle with collaboration and receiving feedback."
        ),
        "ideal_business_model": (
            "Solo expert brands, personal coaching, consulting, or any model where their "
            "individual authority is the product. Avoid committee-driven structures."
        ),
        "marketing_style": (
            "Bold, direct, and personal. Marketing that positions them as THE authority — "
            "not one of many. Personal brand over company brand. First-person storytelling."
        )
    },
    2: {
        "title": "The Collaborator",
        "leadership_style": (
            "Life Path 2s lead through partnership and diplomacy. They are exceptional at "
            "building teams and creating harmony. Their power is in relationships, not solo authority."
        ),
        "business_strengths": (
            "Emotional intelligence, listening skills, partnership building, mediation, "
            "and the ability to make clients feel deeply seen and understood."
        ),
        "blindspots": (
            "Indecisiveness, people-pleasing, and undervaluing their own contributions. "
            "Can give too much and price too low out of fear of conflict."
        ),
        "ideal_business_model": (
            "Partnership-based ventures, coaching with strong community elements, "
            "consulting that involves facilitation, or service businesses built on trust."
        ),
        "marketing_style": (
            "Warm, relational, and community-focused. Testimonials and social proof are "
            "powerful. Content that makes the audience feel understood and not alone."
        )
    },
    3: {
        "title": "The Communicator",
        "leadership_style": (
            "Life Path 3s lead through inspiration and expression. They energize rooms, "
            "captivate audiences, and make complex ideas feel accessible and exciting."
        ),
        "business_strengths": (
            "Creativity, communication, storytelling, performance, and the ability to "
            "make their brand feel alive and entertaining."
        ),
        "blindspots": (
            "Scattered energy, difficulty finishing projects, and a tendency to start "
            "new ideas before completing existing ones. Can avoid the 'boring' business fundamentals."
        ),
        "ideal_business_model": (
            "Content creation, speaking, coaching with a strong entertainment element, "
            "group programs, and any model that leverages their voice and personality."
        ),
        "marketing_style": (
            "High energy, entertaining, and story-driven. Video content is their natural medium. "
            "Humor and authenticity resonate more than polished perfection."
        )
    },
    4: {
        "title": "The Builder",
        "leadership_style": (
            "Life Path 4s lead through structure, reliability, and mastery. They build "
            "things that last. Clients trust them because they are consistent and thorough."
        ),
        "business_strengths": (
            "Systems thinking, discipline, attention to detail, follow-through, and the "
            "ability to build sustainable operations that don't depend on chaos."
        ),
        "blindspots": (
            "Rigidity, resistance to change, and a tendency to over-prepare before launching. "
            "Can get stuck in planning mode and delay execution indefinitely."
        ),
        "ideal_business_model": (
            "Productized services, systems-based coaching, training programs with clear "
            "frameworks, and any model that rewards consistency and depth over novelty."
        ),
        "marketing_style": (
            "Educational, process-oriented, and trust-building. Content that demonstrates "
            "expertise through depth. Case studies and step-by-step frameworks perform well."
        )
    },
    5: {
        "title": "The Freedom Seeker",
        "leadership_style": (
            "Life Path 5s lead through adaptability and adventure. They are most effective "
            "in dynamic environments and lose energy in rigid, repetitive structures."
        ),
        "business_strengths": (
            "Versatility, salesmanship, networking, the ability to pivot quickly, and "
            "a natural charisma that draws people in."
        ),
        "blindspots": (
            "Inconsistency, commitment issues, and a tendency to abandon projects when "
            "they stop feeling exciting. Can struggle with the long game."
        ),
        "ideal_business_model": (
            "Variety-based offerings, speaking, travel-integrated work, consulting across "
            "industries, or any model that allows freedom of movement and expression."
        ),
        "marketing_style": (
            "Spontaneous, experiential, and trend-aware. Short-form content, live events, "
            "and real-time engagement. Authenticity over polish."
        )
    },
    6: {
        "title": "The Nurturer",
        "leadership_style": (
            "Life Path 6s lead through care, responsibility, and service. They build "
            "businesses that genuinely improve people's lives and feel called to serve."
        ),
        "business_strengths": (
            "Deep empathy, client retention, community building, and the ability to create "
            "transformational experiences that clients rave about."
        ),
        "blindspots": (
            "Over-giving, difficulty charging what they're worth, and taking on clients' "
            "problems as their own. Burnout is a real risk."
        ),
        "ideal_business_model": (
            "Coaching, healing, education, community-based programs, and any service "
            "model where the transformation of others is the core product."
        ),
        "marketing_style": (
            "Heart-led, values-driven, and transformation-focused. Before-and-after stories, "
            "client testimonials, and content that communicates genuine care."
        )
    },
    7: {
        "title": "The Seeker",
        "leadership_style": (
            "Life Path 7s lead through wisdom and expertise. They are the researchers, "
            "the deep thinkers, the ones clients come to for answers no one else has."
        ),
        "business_strengths": (
            "Analytical depth, intellectual authority, the ability to synthesize complex "
            "information, and a natural gravitas that commands respect."
        ),
        "blindspots": (
            "Isolation, difficulty marketing themselves, and a tendency to over-intellectualize "
            "rather than connect emotionally. Can struggle with visibility."
        ),
        "ideal_business_model": (
            "Expert consulting, research-based products, high-ticket advisory, and any "
            "model that rewards depth of knowledge over breadth of reach."
        ),
        "marketing_style": (
            "Thought leadership, long-form content, podcasts, and written work. "
            "Quality over quantity. Positioning as the expert's expert."
        )
    },
    8: {
        "title": "The Powerhouse",
        "leadership_style": (
            "Life Path 8s are built for business. They understand power, money, and "
            "authority intuitively. They lead with confidence and expect results."
        ),
        "business_strengths": (
            "Financial acumen, executive presence, the ability to think at scale, "
            "and a natural magnetism around wealth and success."
        ),
        "blindspots": (
            "Workaholism, controlling tendencies, and a tendency to measure self-worth "
            "by financial results. Can be perceived as intimidating or transactional."
        ),
        "ideal_business_model": (
            "High-ticket offers, scaling to agency or team model, investments, and any "
            "model that rewards ambition and rewards big thinking."
        ),
        "marketing_style": (
            "Results-focused, aspirational, and authority-driven. Metrics, outcomes, "
            "and transformation at scale. Premium positioning is essential."
        )
    },
    9: {
        "title": "The Humanitarian",
        "leadership_style": (
            "Life Path 9s lead through vision and purpose. They are most powerful when "
            "their business is connected to a mission larger than profit."
        ),
        "business_strengths": (
            "Visionary thinking, universal appeal, the ability to inspire movements, "
            "and a natural wisdom that comes from having lived fully."
        ),
        "blindspots": (
            "Difficulty with endings, giving too much without receiving, and a tendency "
            "to sacrifice personal needs for the greater good."
        ),
        "ideal_business_model": (
            "Mission-driven brands, education, community platforms, and any model "
            "that creates systemic change, not just individual transformation."
        ),
        "marketing_style": (
            "Story-driven, purpose-led, and emotionally resonant. Content that connects "
            "personal experience to universal truth. Legacy over lifestyle."
        )
    },
    11: {
        "title": "The Intuitive Visionary (Master Number)",
        "leadership_style": (
            "Master Number 11s are visionary leaders who operate on intuition and inspiration. "
            "They often sense market shifts before they happen and lead through their ability "
            "to illuminate what others cannot yet see."
        ),
        "business_strengths": (
            "Visionary insight, inspirational communication, the ability to channel ideas "
            "that feel ahead of their time, and a natural magnetism."
        ),
        "blindspots": (
            "Nervous energy, self-doubt despite enormous talent, and a tendency to "
            "oscillate between brilliance and paralysis. The gap between vision and execution is wide."
        ),
        "ideal_business_model": (
            "Thought leadership, speaking, spiritual or transformational coaching, "
            "and any model that allows them to operate as a conduit for bigger ideas."
        ),
        "marketing_style": (
            "Inspirational, visionary, and deeply personal. Content that feels like "
            "a transmission, not a transaction. Authenticity is non-negotiable."
        )
    },
    22: {
        "title": "The Master Builder (Master Number)",
        "leadership_style": (
            "Master Number 22s are the architects of the possible. They have the vision "
            "of an 11 and the execution capacity of a 4. They build empires."
        ),
        "business_strengths": (
            "Ability to think at massive scale, combine vision with practicality, "
            "lead large teams, and create lasting institutions."
        ),
        "blindspots": (
            "Overwhelm from the weight of their own vision, perfectionism, and a tendency "
            "to take on more than any one person can carry."
        ),
        "ideal_business_model": (
            "Scalable platforms, organizations, or movements. Any model designed to "
            "outlast the founder and create generational impact."
        ),
        "marketing_style": (
            "Legacy-focused, ambitious, and visionary. Content that communicates "
            "the scale of the mission, not just the immediate offer."
        )
    },
    33: {
        "title": "The Master Teacher (Master Number)",
        "leadership_style": (
            "Master Number 33s lead through unconditional service and teaching. "
            "They are rare and carry a responsibility to uplift humanity through their work."
        ),
        "business_strengths": (
            "Deep compassion, masterful teaching ability, the capacity to heal and "
            "transform at a profound level, and universal appeal."
        ),
        "blindspots": (
            "Martyrdom, self-sacrifice to the point of depletion, and difficulty "
            "maintaining boundaries with clients or causes."
        ),
        "ideal_business_model": (
            "Education, healing arts, spiritual leadership, and any model where "
            "the transformation of others is the highest calling."
        ),
        "marketing_style": (
            "Deeply human, compassionate, and purpose-driven. Content that teaches "
            "and heals simultaneously. The message IS the marketing."
        )
    }
}


def reduce_to_single_digit(n: int) -> int:
    """Reduce a number to a single digit, preserving master numbers 11, 22, 33."""
    while n > 9 and n not in MASTER_NUMBERS:
        n = sum(int(d) for d in str(n))
    return n


def calculate_life_path(birthday_str: str) -> dict:
    """
    Calculate Life Path Number from a birthday string (YYYY-MM-DD).

    Example: 1981-07-14 → 1+9+8+1+0+7+1+4 = 31 → 3+1 = 4
    """
    try:
        bday = date.fromisoformat(birthday_str)
    except (ValueError, TypeError):
        return {"error": f"Invalid birthday format: {birthday_str}. Expected YYYY-MM-DD."}

    digits = [int(d) for d in birthday_str.replace("-", "") if d.isdigit()]
    total = sum(digits)
    life_path = reduce_to_single_digit(total)

    calculation_str = (
        f"{'+'.join(str(d) for d in digits)} = {total} → "
        f"{'+'.join(str(d) for d in str(total))} = {life_path}"
        if total > 9 and total not in MASTER_NUMBERS
        else f"{'+'.join(str(d) for d in digits)} = {total}"
    )

    profile = LIFE_PATH_PROFILES.get(life_path, {})

    return {
        "birthday": birthday_str,
        "calculation": calculation_str,
        "life_path_number": life_path,
        "is_master_number": life_path in MASTER_NUMBERS,
        "title": profile.get("title", f"Life Path {life_path}"),
        "leadership_style": profile.get("leadership_style", ""),
        "business_strengths": profile.get("business_strengths", ""),
        "blindspots": profile.get("blindspots", ""),
        "ideal_business_model": profile.get("ideal_business_model", ""),
        "marketing_style": profile.get("marketing_style", "")
    }


# ─────────────────────────────────────────────────────────────
# Human Design Type
# ─────────────────────────────────────────────────────────────

HUMAN_DESIGN_PROFILES = {
    "Generator": {
        "strategy": "Wait to Respond",
        "authority_description": (
            "Generators make best decisions by waiting for life to present opportunities "
            "and responding with their gut. Initiating from the mind leads to frustration."
        ),
        "marketing_approach": (
            "Show up consistently and let your energy attract. Content that responds to "
            "real questions your audience is asking. Engagement-driven visibility."
        ),
        "energy_management": (
            "Generators have sustainable energy when doing work they love. "
            "The key is to notice when something feels like a 'hell yes' vs. obligation. "
            "Depletion comes from doing work that doesn't light them up."
        ),
        "workday_structure": (
            "Front-load creative and high-energy work in the morning. "
            "Respond to opportunities as they arise rather than forcing a rigid schedule. "
            "Rest fully when tired — don't push through exhaustion."
        ),
        "entrepreneurial_traps": (
            "Initiating from frustration, taking on projects that don't excite them, "
            "and ignoring their sacral gut response in favor of mental logic."
        )
    },
    "Manifesting Generator": {
        "strategy": "Wait to Respond, then Inform",
        "authority_description": (
            "Manifesting Generators are multi-passionate and fast-moving. "
            "They respond to opportunities, then inform others before acting. "
            "Skipping the inform step creates resistance and pushback."
        ),
        "marketing_approach": (
            "Multi-format content across platforms. Show the full range of your interests. "
            "Speed and variety are assets, not liabilities. Build in public."
        ),
        "energy_management": (
            "MGs have bursts of intense energy followed by periods of rest. "
            "Honor the cycles. Multi-tasking is natural for them — don't force single focus."
        ),
        "workday_structure": (
            "Work in sprints. Multiple projects simultaneously is fine. "
            "Build in white space for pivots. Don't over-schedule."
        ),
        "entrepreneurial_traps": (
            "Starting too many things, not finishing, and feeling guilty about pivoting. "
            "Also: not informing their audience/team before making big moves."
        )
    },
    "Projector": {
        "strategy": "Wait for the Invitation",
        "authority_description": (
            "Projectors are here to guide and direct others. They work best when invited "
            "into opportunities rather than initiating. Recognition must come before invitation."
        ),
        "marketing_approach": (
            "Position as the expert guide. Thought leadership, speaking, and being seen "
            "as the authority in your niche. Let your expertise invite clients to you."
        ),
        "energy_management": (
            "Projectors have limited and non-sustainable energy. Deep rest is essential. "
            "Working in focused bursts rather than long hours is more effective."
        ),
        "workday_structure": (
            "Shorter, focused work sessions. Protect energy by limiting client load. "
            "High-value, high-touch work over high-volume output."
        ),
        "entrepreneurial_traps": (
            "Initiating without invitation, over-working, and feeling bitter when "
            "their guidance is ignored or unrecognized."
        )
    },
    "Manifestor": {
        "strategy": "Inform before Acting",
        "authority_description": (
            "Manifestors are the initiators of the Human Design system. "
            "They are here to start things and create impact. "
            "Informing others before acting reduces resistance."
        ),
        "marketing_approach": (
            "Bold, direct, and unapologetic. Launch first, explain later. "
            "Your confidence and certainty IS the marketing."
        ),
        "energy_management": (
            "Manifestors have non-sustainable energy and need significant rest cycles. "
            "They initiate, then rest while others respond and execute."
        ),
        "workday_structure": (
            "Work in powerful bursts of initiation followed by deep rest. "
            "Delegate execution to others. Focus on vision and launch."
        ),
        "entrepreneurial_traps": (
            "Not informing others before major moves, creating anger and resistance. "
            "Also: trying to sustain energy like a Generator and burning out."
        )
    },
    "Reflector": {
        "strategy": "Wait a Lunar Cycle (28 days) for Major Decisions",
        "authority_description": (
            "Reflectors are rare and deeply sensitive to their environment. "
            "They reflect the health of the communities they're in. "
            "Major decisions require a full lunar cycle to process."
        ),
        "marketing_approach": (
            "Community-centered content. Reflect back what your audience is experiencing. "
            "Your unique perspective as an observer is your greatest asset."
        ),
        "energy_management": (
            "Reflectors are highly sensitive to environments. Choosing the right "
            "physical and social environment is paramount to their well-being and effectiveness."
        ),
        "workday_structure": (
            "Flexible, environment-sensitive scheduling. Avoid rigid routines. "
            "Work where and when the environment feels right."
        ),
        "entrepreneurial_traps": (
            "Making major decisions too quickly, staying in environments that deplete them, "
            "and trying to be consistent in ways that don't honor their nature."
        )
    }
}


def estimate_human_design_type(birthday_str: str, birth_time: Optional[str],
                                birth_location: Optional[str]) -> dict:
    """
    Estimate Human Design Type.

    Full Human Design calculation requires precise birth time and location
    and access to an ephemeris. Without birth time, we provide a general
    framework and recommend the subject get a full chart reading.

    With birth time + location, we use a simplified heuristic based on
    birth date patterns (a full implementation would use an ephemeris API).
    """
    if not birth_time:
        return {
            "available": False,
            "reason": (
                "Birth time was not provided. A precise Human Design chart requires "
                "exact birth time and location. Recommend subject provide birth time "
                "for a full Human Design reading."
            ),
            "recommendation": (
                "Visit mybodygraph.com or jovianarchive.com with your exact birth time "
                "to discover your Human Design Type and Authority."
            )
        }

    # With birth time available, we can provide the framework
    # In a production system, this would call an ephemeris API
    # For now, we provide the full framework and note the limitation
    try:
        bday = date.fromisoformat(birthday_str)
        # Simplified type estimation based on birth year + month patterns
        # (This is a placeholder — production should use ephem/astropy or an HD API)
        year_mod = bday.year % 5
        type_map = {
            0: "Generator",
            1: "Manifesting Generator",
            2: "Projector",
            3: "Manifestor",
            4: "Generator"  # Generators are ~70% of population
        }
        estimated_type = type_map.get(year_mod, "Generator")
        profile_data = HUMAN_DESIGN_PROFILES.get(estimated_type, {})

        return {
            "available": True,
            "estimated": True,
            "note": (
                "Human Design Type shown is an approximation. "
                "For a precise reading, visit mybodygraph.com with exact birth time."
            ),
            "type": estimated_type,
            "birth_time_provided": birth_time,
            "birth_location": birth_location,
            "strategy": profile_data.get("strategy", ""),
            "authority_description": profile_data.get("authority_description", ""),
            "marketing_approach": profile_data.get("marketing_approach", ""),
            "energy_management": profile_data.get("energy_management", ""),
            "workday_structure": profile_data.get("workday_structure", ""),
            "entrepreneurial_traps": profile_data.get("entrepreneurial_traps", "")
        }

    except Exception as e:
        return {
            "available": False,
            "reason": f"Could not calculate Human Design: {str(e)}"
        }


# ─────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────

def run_archetypal_profile(birthday: Optional[str],
                           birth_time: Optional[str],
                           birth_location: Optional[str]) -> dict:
    """
    Generate full archetypal profile from available birth data.

    Args:
        birthday: YYYY-MM-DD string
        birth_time: HH:MM string (24h) or None
        birth_location: city/state/country string or None

    Returns:
        dict with full archetypal profile
    """
    profile = {
        "numerology": None,
        "human_design": None,
        "available": False,
        "summary": ""
    }

    if not birthday:
        profile["summary"] = (
            "No birthday was provided. Archetypal profiling was not available for this session. "
            "Recommend the subject provide birth data for an enhanced version of their Blueprint."
        )
        return profile

    profile["available"] = True

    # Numerology
    profile["numerology"] = calculate_life_path(birthday)

    # Human Design
    profile["human_design"] = estimate_human_design_type(birthday, birth_time, birth_location)

    # Summary
    lp = profile["numerology"].get("life_path_number")
    lp_title = profile["numerology"].get("title", "")
    hd_type = profile["human_design"].get("type", "Not determined") if profile["human_design"].get("available") else "Not available (no birth time)"

    profile["summary"] = (
        f"Life Path {lp} — {lp_title}. "
        f"Human Design Type: {hd_type}."
    )

    return profile


# ─────────────────────────────────────────────────────────────
# Standalone test
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    result = run_archetypal_profile(
        birthday="1981-07-14",
        birth_time=None,
        birth_location="San Antonio, Texas"
    )
    print(json.dumps(result, indent=2))
