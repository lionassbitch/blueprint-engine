#!/usr/bin/env python3
"""
BLUEPRINT ENGINE ORCHESTRATOR
Exsuvera LLC / Lion Ass Bitch (LAB)

Autonomous post-session pipeline that transforms a Blueprint Session transcript
into a comprehensive, personalized, branded business plan and delivers it.

Usage:
    python3 orchestrator.py --payload sample_data/marcus_rivera_payload.json \
                            --transcript sample_data/marcus_rivera_transcript.txt

    python3 orchestrator.py --payload path/to/payload.json \
                            --transcript path/to/transcript.txt \
                            [--output-dir path/to/output] \
                            [--skip-social] \
                            [--skip-email]
"""

import argparse
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

# ── Ensure modules directory is on path ──────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "modules"))

from task1_social_audit import run_social_audit
from task2_archetypal_profile import run_archetypal_profile
from task3_blueprint_engine import run_blueprint_engine
from task4_document_formatter import run_document_formatter
from task5_delivery_logging import run_delivery_and_logging

# ─────────────────────────────────────────────────────────────
# Logging setup
# ─────────────────────────────────────────────────────────────

def setup_logging(output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    log_path = os.path.join(output_dir, f"pipeline_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_path)
        ]
    )
    return log_path


logger = logging.getLogger("BlueprintEngine")


# ─────────────────────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────────────────────

def run_pipeline(payload: dict, transcript: str,
                 output_dir: str = "/home/ubuntu/blueprint_engine/output",
                 skip_social: bool = False,
                 skip_email: bool = False) -> dict:
    """
    Execute the full 5-task Blueprint Engine pipeline.

    Args:
        payload: Session payload dict (contact, social handles, metadata, etc.)
        transcript: Full transcript text
        output_dir: Directory for all output files
        skip_social: Skip social media audit (useful for testing)
        skip_email: Skip email delivery (useful for testing)

    Returns:
        dict with all pipeline results and completion report
    """
    os.makedirs(output_dir, exist_ok=True)
    pipeline_start = datetime.utcnow()

    contact = payload.get("contact", {})
    social_handles = payload.get("social_handles", [])
    website_url = payload.get("website")
    birthday = payload.get("birthday")
    birth_time = payload.get("birth_time")
    birth_location = payload.get("birth_location")
    session_metadata = payload.get("session_metadata", {})
    notification_email = payload.get("notification_email", "eddie@exsuvera.com")

    first_name = contact.get("first_name", "")
    last_name = contact.get("last_name", "")
    session_date = session_metadata.get("session_date", datetime.utcnow().strftime("%Y-%m-%d"))

    logger.info("=" * 60)
    logger.info("BLUEPRINT ENGINE — PIPELINE STARTING")
    logger.info(f"Subject: {first_name} {last_name}")
    logger.info(f"Session date: {session_date}")
    logger.info("=" * 60)

    results = {}

    # ══════════════════════════════════════════════════════════
    # TASK 1: SOCIAL MEDIA AUDIT
    # ══════════════════════════════════════════════════════════
    logger.info("\n── TASK 1: Social Media Audit ──────────────────────────")
    try:
        if skip_social or not social_handles:
            if not social_handles:
                logger.info("No social handles provided. Skipping social audit.")
            else:
                logger.info("Social audit skipped (--skip-social flag).")
            social_audit = {
                "audit_timestamp": datetime.utcnow().isoformat() + "Z",
                "profiles": [],
                "website": None,
                "gap_analysis": "",
                "platform_prioritization": "",
                "content_to_conversion_assessment": "",
                "summary": "No social media handles were provided. Audit skipped."
            }
        else:
            social_audit = run_social_audit(
                social_handles=social_handles,
                website_url=website_url,
                business_vision=""  # Will be filled from transcript extraction
            )
        results["social_audit"] = social_audit
        social_audit_path = os.path.join(output_dir, "social_audit.json")
        with open(social_audit_path, "w") as f:
            json.dump(social_audit, f, indent=2)
        logger.info(f"Task 1 complete. {social_audit.get('summary', '')}")
    except Exception as e:
        logger.error(f"Task 1 error: {e}\n{traceback.format_exc()}")
        social_audit = {"error": str(e), "profiles": [], "summary": f"Audit failed: {str(e)}"}
        results["social_audit"] = social_audit

    # ══════════════════════════════════════════════════════════
    # TASK 2: ARCHETYPAL PROFILING
    # ══════════════════════════════════════════════════════════
    logger.info("\n── TASK 2: Archetypal Profiling ────────────────────────")
    try:
        archetypal_profile = run_archetypal_profile(
            birthday=birthday,
            birth_time=birth_time,
            birth_location=birth_location
        )
        results["archetypal_profile"] = archetypal_profile
        archetype_path = os.path.join(output_dir, "archetypal_profile.json")
        with open(archetype_path, "w") as f:
            json.dump(archetypal_profile, f, indent=2)
        logger.info(f"Task 2 complete. {archetypal_profile.get('summary', '')}")
    except Exception as e:
        logger.error(f"Task 2 error: {e}\n{traceback.format_exc()}")
        archetypal_profile = {"error": str(e), "available": False, "summary": f"Profiling failed: {str(e)}"}
        results["archetypal_profile"] = archetypal_profile

    # ══════════════════════════════════════════════════════════
    # TASK 3: BLUEPRINT ENGINE (3-STAGE CLAUDE PIPELINE)
    # ══════════════════════════════════════════════════════════
    logger.info("\n── TASK 3: Blueprint Engine (Claude AI Pipeline) ───────")
    try:
        blueprint_result = run_blueprint_engine(
            transcript=transcript,
            social_audit=social_audit,
            archetypal_profile=archetypal_profile,
            output_dir=output_dir
        )
        results["blueprint"] = blueprint_result
        stage1_data = blueprint_result["stage1_data"]
        stage2_data = blueprint_result["stage2_data"]
        business_plan_md = blueprint_result["business_plan_markdown"]

        # Extract business name from Stage 1 data
        business_info = stage1_data.get("business", {})
        business_name = business_info.get("name") if isinstance(business_info, dict) else None
        business_name = business_name or "Your Business"

        # Extract business concept for notification
        business_pitch = business_info.get("pitch", "") if isinstance(business_info, dict) else ""
        business_concept = business_pitch[:150] if business_pitch else business_name

        logger.info(f"Task 3 complete. Business: {business_name}")
    except Exception as e:
        logger.error(f"Task 3 error: {e}\n{traceback.format_exc()}")
        # Create minimal fallback data
        business_name = f"{first_name}'s Business"
        business_concept = "Business plan generation failed"
        business_plan_md = f"# Blueprint for {first_name} {last_name}\n\n*Pipeline error: {str(e)}*"
        stage1_data = {}
        stage2_data = {}
        blueprint_result = {
            "stage1_data": stage1_data,
            "stage2_data": stage2_data,
            "business_plan_markdown": business_plan_md,
            "stage1_path": None,
            "stage2_path": None,
            "plan_path": None
        }
        results["blueprint"] = blueprint_result

    # ══════════════════════════════════════════════════════════
    # TASK 4: DOCUMENT FORMATTING
    # ══════════════════════════════════════════════════════════
    logger.info("\n── TASK 4: Document Formatting ─────────────────────────")
    try:
        doc_result = run_document_formatter(
            markdown_content=business_plan_md,
            subject_first_name=first_name,
            subject_last_name=last_name,
            business_name=business_name,
            session_date=session_date,
            output_dir=output_dir
        )
        results["document"] = doc_result
        pdf_path = doc_result.get("pdf_path")
        html_path = doc_result.get("html_path")
        pdf_filename = doc_result.get("filename", f"Blueprint_{last_name}_{session_date}.pdf")
        logger.info(f"Task 4 complete. PDF: {pdf_path or 'failed'} | HTML: {html_path}")
    except Exception as e:
        logger.error(f"Task 4 error: {e}\n{traceback.format_exc()}")
        pdf_path = None
        html_path = None
        pdf_filename = f"Blueprint_{last_name}_{session_date}.pdf"
        results["document"] = {"error": str(e)}

    # ══════════════════════════════════════════════════════════
    # TASK 5: DELIVERY & LOGGING
    # ══════════════════════════════════════════════════════════
    logger.info("\n── TASK 5: Delivery & Logging ──────────────────────────")
    try:
        # Locate transcript file path if it was saved
        transcript_path = os.path.join(output_dir, "transcript.txt")
        with open(transcript_path, "w") as f:
            f.write(transcript)

        delivery_result = run_delivery_and_logging(
            contact=contact,
            session_metadata=session_metadata,
            business_name=business_name,
            business_concept=business_concept,
            pdf_path=pdf_path,
            html_path=html_path,
            pdf_filename=pdf_filename,
            stage1_data=stage1_data,
            stage2_data=stage2_data,
            social_audit=social_audit,
            archetypal_profile=archetypal_profile,
            transcript_path=transcript_path,
            stage1_path=blueprint_result.get("stage1_path"),
            stage2_path=blueprint_result.get("stage2_path"),
            plan_path=blueprint_result.get("plan_path"),
            notification_email=notification_email,
            output_dir=output_dir
        )
        results["delivery"] = delivery_result
        completion_report = delivery_result.get("completion_report", "Pipeline complete.")
        logger.info(f"Task 5 complete.")
    except Exception as e:
        logger.error(f"Task 5 error: {e}\n{traceback.format_exc()}")
        completion_report = f"Pipeline completed with delivery errors: {str(e)}"
        results["delivery"] = {"error": str(e)}

    # ══════════════════════════════════════════════════════════
    # FINAL STATUS REPORT
    # ══════════════════════════════════════════════════════════
    pipeline_end = datetime.utcnow()
    duration_seconds = (pipeline_end - pipeline_start).total_seconds()

    logger.info("\n" + "=" * 60)
    logger.info(completion_report)
    logger.info("=" * 60)
    logger.info(f"Total pipeline duration: {duration_seconds:.1f} seconds")

    results["completion_report"] = completion_report
    results["pipeline_duration_seconds"] = duration_seconds
    results["output_dir"] = output_dir

    return results


# ─────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Blueprint Engine Orchestrator — Exsuvera LLC / LAB"
    )
    parser.add_argument(
        "--payload", required=True,
        help="Path to session payload JSON file"
    )
    parser.add_argument(
        "--transcript", required=True,
        help="Path to session transcript text file"
    )
    parser.add_argument(
        "--output-dir", default="/home/ubuntu/blueprint_engine/output",
        help="Directory for output files (default: ./output)"
    )
    parser.add_argument(
        "--skip-social", action="store_true",
        help="Skip social media audit (useful for testing)"
    )
    parser.add_argument(
        "--skip-email", action="store_true",
        help="Skip email delivery (useful for testing)"
    )
    args = parser.parse_args()

    # Setup logging
    log_path = setup_logging(args.output_dir)
    logger.info(f"Log file: {log_path}")

    # Load payload
    with open(args.payload, "r") as f:
        payload = json.load(f)

    # Load transcript
    with open(args.transcript, "r") as f:
        transcript = f.read()

    # Run pipeline
    results = run_pipeline(
        payload=payload,
        transcript=transcript,
        output_dir=args.output_dir,
        skip_social=args.skip_social,
        skip_email=args.skip_email
    )

    print("\n" + results.get("completion_report", "Pipeline complete."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
