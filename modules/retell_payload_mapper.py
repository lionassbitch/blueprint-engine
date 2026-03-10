#!/usr/bin/env python3
"""
BLUEPRINT ENGINE — Retell Payload Mapper
Exsuvera LLC / Lion Ass Bitch (LAB)

Converts a Retell AI `call` object (from the call_analyzed webhook)
into the standard Blueprint Engine pipeline payload.

Two modes:
  1. STRUCTURED MODE (preferred):
     Reads contact fields directly from call.call_analysis — the structured
     data Retell extracts using your Post-Call Analysis configuration.
     Fast, reliable, no extra API call needed.

  2. FALLBACK MODE:
     If call_analysis fields are missing or incomplete, uses Claude to
     extract contact fields from the raw transcript text.
     Slower (~20-30s) but requires zero Retell configuration.
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Optional

logger = logging.getLogger("RetellPayloadMapper")


# ─────────────────────────────────────────────────────────────
# Field names expected in call.call_analysis
# These must match exactly what you named them in Retell's
# Post-Call Analysis dashboard.
# ─────────────────────────────────────────────────────────────
ANALYSIS_FIELD_MAP = {
    "first_name":      "contact.first_name",
    "last_name":       "contact.last_name",
    "email":           "contact.email",
    "phone":           "contact.phone",
    "location":        "contact.location",
    "birthday":        "birthday",
    "birth_time":      "birth_time",
    "birth_location":  "birth_location",
    "website":         "website",
    "instagram":       "social_handles.instagram",
    "youtube":         "social_handles.youtube",
    "facebook":        "social_handles.facebook",
    "linkedin":        "social_handles.linkedin",
    "tiktok":          "social_handles.tiktok",
}


def map_retell_to_pipeline_payload(call: dict, transcript: str) -> dict:
    """
    Convert a Retell call object into a Blueprint Engine pipeline payload.

    Args:
        call: The full call object from Retell's call_analyzed webhook
        transcript: The full transcript string

    Returns:
        A pipeline payload dict ready for run_pipeline()
    """
    call_analysis = call.get("call_analysis", {}) or {}
    call_id = call.get("call_id", "unknown")
    start_ts = call.get("start_timestamp")
    end_ts = call.get("end_timestamp")

    # Calculate duration
    duration_minutes = None
    if start_ts and end_ts:
        duration_minutes = round((end_ts - start_ts) / 60000)  # ms → minutes

    session_date = datetime.utcnow().strftime("%Y-%m-%d")
    if start_ts:
        session_date = datetime.utcfromtimestamp(start_ts / 1000).strftime("%Y-%m-%d")

    # ── Try structured mode first ─────────────────────────────
    has_structured_data = bool(call_analysis) and any(
        call_analysis.get(field) for field in ["first_name", "email", "last_name"]
    )

    if has_structured_data:
        logger.info(f"Call {call_id}: Using structured Post-Call Analysis fields.")
        contact_data, social_handles, extra = _extract_from_analysis(call_analysis)
    else:
        logger.info(f"Call {call_id}: No structured analysis fields found. Falling back to Claude extraction.")
        contact_data, social_handles, extra = _extract_from_transcript_via_claude(transcript)

    # ── Build payload ─────────────────────────────────────────
    payload = {
        "session_metadata": {
            "session_date": session_date,
            "duration_minutes": duration_minutes,
            "call_id": call_id,
            "recording_url": call.get("recording_url"),
            "disconnection_reason": call.get("disconnection_reason"),
            "from_number": call.get("from_number"),
            "to_number": call.get("to_number"),
        },
        "contact": {
            "first_name": contact_data.get("first_name", ""),
            "last_name": contact_data.get("last_name", ""),
            "email": contact_data.get("email", ""),
            "phone": contact_data.get("phone") or call.get("from_number", ""),
            "location": contact_data.get("location", ""),
        },
        "social_handles": _build_social_handles(social_handles),
        "website": extra.get("website") or "",
        "birthday": extra.get("birthday") or "",
        "birth_time": extra.get("birth_time") or None,
        "birth_location": extra.get("birth_location") or None,
        "notification_email": os.environ.get("EDDIE_EMAIL", "eddie@exsuvera.com"),
        # Pass through any Retell metadata for logging
        "_retell_call_id": call_id,
        "_retell_agent_id": call.get("agent_id"),
        "_extraction_mode": "structured" if has_structured_data else "claude_fallback",
    }

    # Log what we extracted
    name = f"{payload['contact']['first_name']} {payload['contact']['last_name']}".strip()
    email = payload['contact']['email']
    logger.info(f"Call {call_id}: Mapped payload — Name: '{name}', Email: '{email}', "
                f"Social handles: {len(payload['social_handles'])}, "
                f"Birthday: '{payload['birthday']}'")

    return payload


# ─────────────────────────────────────────────────────────────
# Mode 1: Extract from Retell Post-Call Analysis fields
# ─────────────────────────────────────────────────────────────

def _extract_from_analysis(call_analysis: dict) -> tuple:
    """Extract contact data from Retell's structured call_analysis fields."""
    contact = {
        "first_name": _clean(call_analysis.get("first_name")),
        "last_name":  _clean(call_analysis.get("last_name")),
        "email":      _clean(call_analysis.get("email")),
        "phone":      _clean(call_analysis.get("phone")),
        "location":   _clean(call_analysis.get("location")),
    }
    social = {
        "instagram": _clean(call_analysis.get("instagram")),
        "youtube":   _clean(call_analysis.get("youtube")),
        "facebook":  _clean(call_analysis.get("facebook")),
        "linkedin":  _clean(call_analysis.get("linkedin")),
        "tiktok":    _clean(call_analysis.get("tiktok")),
    }
    extra = {
        "website":        _clean(call_analysis.get("website")),
        "birthday":       _normalize_date(call_analysis.get("birthday")),
        "birth_time":     _clean(call_analysis.get("birth_time")),
        "birth_location": _clean(call_analysis.get("birth_location")),
    }
    return contact, social, extra


# ─────────────────────────────────────────────────────────────
# Mode 2: Extract from raw transcript via Claude
# ─────────────────────────────────────────────────────────────

def _extract_from_transcript_via_claude(transcript: str) -> tuple:
    """
    Use Claude to extract contact fields from the raw transcript.
    This is the fallback when Retell Post-Call Analysis is not configured.
    """
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

        prompt = f"""Extract the following information from this call transcript.
Return ONLY a valid JSON object with these exact keys.
If a field was not mentioned or is unknown, use null.
Do not add any text before or after the JSON.

Keys to extract:
- first_name: string
- last_name: string  
- email: string (exact email address as spoken/spelled)
- phone: string
- location: string (city, state)
- birthday: string (YYYY-MM-DD format — convert from any spoken format)
- birth_time: string (HH:MM 24hr format — convert from spoken, e.g. "2:30 PM" → "14:30")
- birth_location: string (city/country of birth)
- website: string (full URL)
- instagram: string (handle without @)
- youtube: string (channel handle without @)
- facebook: string (page name or URL)
- linkedin: string (profile URL)
- tiktok: string (handle without @)

TRANSCRIPT:
{transcript[:8000]}

JSON:"""

        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = response.content[0].text.strip()
        # Strip markdown code fences if present
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)

        extracted = json.loads(raw)
        logger.info("Claude extraction successful.")

        contact = {
            "first_name": _clean(extracted.get("first_name")),
            "last_name":  _clean(extracted.get("last_name")),
            "email":      _clean(extracted.get("email")),
            "phone":      _clean(extracted.get("phone")),
            "location":   _clean(extracted.get("location")),
        }
        social = {
            "instagram": _clean(extracted.get("instagram")),
            "youtube":   _clean(extracted.get("youtube")),
            "facebook":  _clean(extracted.get("facebook")),
            "linkedin":  _clean(extracted.get("linkedin")),
            "tiktok":    _clean(extracted.get("tiktok")),
        }
        extra = {
            "website":        _clean(extracted.get("website")),
            "birthday":       _normalize_date(extracted.get("birthday")),
            "birth_time":     _clean(extracted.get("birth_time")),
            "birth_location": _clean(extracted.get("birth_location")),
        }
        return contact, social, extra

    except Exception as e:
        logger.error(f"Claude extraction failed: {e}. Returning empty contact data.")
        empty = {}
        return empty, empty, empty


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _clean(value) -> Optional[str]:
    """Strip whitespace and return None for null-like values."""
    if value is None:
        return None
    s = str(value).strip()
    if s.lower() in ("null", "none", "n/a", "na", "unknown", "", "not provided", "not mentioned"):
        return None
    return s


def _normalize_date(value) -> Optional[str]:
    """Attempt to normalize a date string to YYYY-MM-DD."""
    if not value:
        return None
    s = _clean(value)
    if not s:
        return None
    # Already in correct format
    if re.match(r'^\d{4}-\d{2}-\d{2}$', s):
        return s
    # Try common formats
    for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y",
                "%m-%d-%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Return as-is if we can't parse
    logger.warning(f"Could not normalize date: '{s}' — returning as-is")
    return s


def _build_social_handles(social: dict) -> list:
    """Convert social dict to the list format the pipeline expects."""
    handles = []
    platform_map = {
        "instagram": "instagram",
        "youtube":   "youtube",
        "facebook":  "facebook",
        "linkedin":  "linkedin",
        "tiktok":    "tiktok",
    }
    for key, platform in platform_map.items():
        handle = social.get(key)
        if handle:
            handles.append({"platform": platform, "handle": handle})
    return handles
