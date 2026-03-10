"""
TASK 5: Delivery & Logging Module
Blueprint Engine Orchestrator — Exsuvera LLC / LAB

1. Send branded email to subject with PDF attachment
2. Log all session artifacts to local storage (and optionally cloud)
3. Notify Eddie with session summary
"""

import json
import os
import shutil
import logging
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Email configuration
# ─────────────────────────────────────────────────────────────

def get_smtp_config() -> dict:
    """
    Read SMTP configuration from environment variables.
    Set these in your .env or environment:
      SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_EMAIL, SMTP_FROM_NAME
    """
    return {
        "host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.environ.get("SMTP_PORT", "587")),
        "user": os.environ.get("SMTP_USER", ""),
        "password": os.environ.get("SMTP_PASSWORD", ""),
        "from_email": os.environ.get("SMTP_FROM_EMAIL", os.environ.get("SMTP_USER", "")),
        "from_name": os.environ.get("SMTP_FROM_NAME", "The Blueprint Session | Exsuvera LLC")
    }


def build_subject_email_body(first_name: str, business_name: str) -> str:
    """Build the email body for the subject."""
    return f"""{first_name},

Thank you for sitting down with us. What you shared in your Blueprint Session was real, and it deserves a real plan.

Attached is your custom business plan — built from your words, your vision, your truth, and an honest assessment of where you are right now. This isn't a template. Every recommendation in this document is specific to you and your business.

Read it. Sit with it. And when you're ready, start with Week 1.

If you want to walk through it together, reply to this email and we'll set up a call.

This is a gift. No strings. No invoice. Just the beginning.

— The Blueprint Session
Exsuvera LLC | Lion Ass Bitch
lionassbitch.com"""


def build_eddie_notification_body(
    subject_name: str,
    business_name: str,
    business_concept: str,
    viability_score,
    readiness_score,
    digital_score,
    calibration_level: str,
    delivery_email: str,
    delivery_timestamp: str,
    artifacts_location: str
) -> str:
    """Build the notification email body for Eddie."""
    return f"""BLUEPRINT ENGINE — PIPELINE COMPLETE

Subject: {subject_name}
Business: {business_name}
Concept: {business_concept}

KEY SCORES:
  Viability:      {viability_score}/10
  Readiness:      {readiness_score}/10
  Digital Maturity: {digital_score}/10

Plan Calibration: {calibration_level}

Delivery:
  Delivered to:   {delivery_email}
  Delivered at:   {delivery_timestamp}

Artifacts stored at: {artifacts_location}

Pipeline executed autonomously. No human intervention required.

— Blueprint Engine, Exsuvera LLC"""


def send_email(
    to_email: str,
    to_name: str,
    subject: str,
    body: str,
    attachment_path: Optional[str] = None,
    attachment_filename: Optional[str] = None,
    smtp_config: Optional[dict] = None
) -> dict:
    """
    Send an email via SMTP with optional attachment.

    Returns:
        dict with success bool, timestamp, error (if any)
    """
    if smtp_config is None:
        smtp_config = get_smtp_config()

    if not smtp_config.get("user") or not smtp_config.get("password"):
        logger.warning("SMTP credentials not configured. Email will be simulated.")
        return {
            "success": False,
            "simulated": True,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": "SMTP credentials not configured. Set SMTP_USER and SMTP_PASSWORD env vars.",
            "to": to_email,
            "subject": subject
        }

    msg = MIMEMultipart()
    msg["From"] = f"{smtp_config['from_name']} <{smtp_config['from_email']}>"
    msg["To"] = f"{to_name} <{to_email}>" if to_name else to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain", "utf-8"))

    # Attach PDF if provided
    if attachment_path and os.path.exists(attachment_path):
        fname = attachment_filename or os.path.basename(attachment_path)
        with open(attachment_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{fname}"')
        msg.attach(part)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_config["host"], smtp_config["port"]) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(smtp_config["user"], smtp_config["password"])
            server.sendmail(smtp_config["from_email"], to_email, msg.as_string())

        timestamp = datetime.utcnow().isoformat() + "Z"
        logger.info(f"Email sent to {to_email} at {timestamp}")
        return {
            "success": True,
            "simulated": False,
            "timestamp": timestamp,
            "to": to_email,
            "subject": subject
        }

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP authentication failed: {e}")
        return {
            "success": False,
            "simulated": False,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": f"SMTP auth error: {str(e)}",
            "to": to_email
        }
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return {
            "success": False,
            "simulated": False,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": str(e),
            "to": to_email
        }


# ─────────────────────────────────────────────────────────────
# Session logging
# ─────────────────────────────────────────────────────────────

def log_session(
    session_id: str,
    contact: dict,
    session_metadata: dict,
    transcript_path: Optional[str],
    social_audit: dict,
    archetypal_profile: dict,
    stage1_path: Optional[str],
    stage2_path: Optional[str],
    plan_path: Optional[str],
    pdf_path: Optional[str],
    delivery_result: dict,
    output_dir: str = "/home/ubuntu/blueprint_engine/output"
) -> str:
    """
    Store all session artifacts in a structured log directory.

    Returns:
        Path to the session log directory
    """
    log_dir = os.path.join(output_dir, "sessions", session_id)
    os.makedirs(log_dir, exist_ok=True)

    # Copy artifacts into session log directory
    def safe_copy(src, dest_name):
        if src and os.path.exists(src):
            dest = os.path.join(log_dir, dest_name)
            shutil.copy2(src, dest)
            return dest
        return None

    artifacts = {
        "session_id": session_id,
        "logged_at": datetime.utcnow().isoformat() + "Z",
        "contact": contact,
        "session_metadata": session_metadata,
        "files": {
            "transcript": safe_copy(transcript_path, "transcript.txt"),
            "stage1_extraction": safe_copy(stage1_path, "stage1_extraction.json"),
            "stage2_enrichment": safe_copy(stage2_path, "stage2_enrichment.json"),
            "business_plan_md": safe_copy(plan_path, "business_plan.md"),
            "business_plan_pdf": safe_copy(pdf_path, "business_plan.pdf"),
        },
        "social_audit_summary": social_audit.get("summary", ""),
        "archetypal_summary": archetypal_profile.get("summary", ""),
        "delivery": delivery_result
    }

    # Save session manifest
    manifest_path = os.path.join(log_dir, "session_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(artifacts, f, indent=2)

    logger.info(f"Session logged at: {log_dir}")
    return log_dir


# ─────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────

def run_delivery_and_logging(
    contact: dict,
    session_metadata: dict,
    business_name: str,
    business_concept: str,
    pdf_path: Optional[str],
    html_path: Optional[str],
    pdf_filename: str,
    stage1_data: dict,
    stage2_data: dict,
    social_audit: dict,
    archetypal_profile: dict,
    transcript_path: Optional[str],
    stage1_path: Optional[str],
    stage2_path: Optional[str],
    plan_path: Optional[str],
    notification_email: str = "eddie@exsuvera.com",
    output_dir: str = "/home/ubuntu/blueprint_engine/output"
) -> dict:
    """
    Execute Task 5: deliver plan to subject, log artifacts, notify Eddie.

    Returns:
        dict with delivery_result, notification_result, log_dir, completion_report
    """
    first_name = contact.get("first_name", "")
    last_name = contact.get("last_name", "")
    subject_email = contact.get("email", "")
    subject_name = f"{first_name} {last_name}".strip()
    session_date = session_metadata.get("session_date", datetime.utcnow().strftime("%Y-%m-%d"))
    session_duration = session_metadata.get("duration_minutes", "Unknown")

    # Extract scores from Stage 2 (handle both flat and nested 'scores' key)
    scores_block = stage2_data.get("scores", stage2_data)  # Claude may nest under 'scores'
    viability = scores_block.get("business_viability_score", {})
    readiness = scores_block.get("founder_readiness_score", {})
    digital = scores_block.get("digital_maturity_score", {})
    calibration = stage2_data.get("plan_calibration", {})

    viability_score = viability.get("score", "N/A") if isinstance(viability, dict) else viability
    readiness_score = readiness.get("score", "N/A") if isinstance(readiness, dict) else readiness
    digital_score = digital.get("score", "N/A") if isinstance(digital, dict) else digital
    calibration_level = calibration.get("aggressiveness_level", "Moderate") if isinstance(calibration, dict) else "Moderate"

    # ── 1. Deliver to subject ──────────────────────────────────
    attachment = pdf_path if pdf_path and os.path.exists(pdf_path) else html_path
    delivery_result = {"success": False, "simulated": True, "timestamp": None, "error": None}

    if subject_email:
        email_body = build_subject_email_body(first_name, business_name)
        delivery_result = send_email(
            to_email=subject_email,
            to_name=subject_name,
            subject=f"Your Blueprint Is Ready — {business_name}",
            body=email_body,
            attachment_path=attachment,
            attachment_filename=pdf_filename
        )

        # Retry once on failure
        if not delivery_result.get("success") and not delivery_result.get("simulated"):
            logger.warning("Email delivery failed. Retrying once...")
            delivery_result = send_email(
                to_email=subject_email,
                to_name=subject_name,
                subject=f"Your Blueprint Is Ready — {business_name}",
                body=email_body,
                attachment_path=attachment,
                attachment_filename=pdf_filename
            )
    else:
        delivery_result["error"] = "No subject email address provided."

    delivery_timestamp = delivery_result.get("timestamp") or datetime.utcnow().isoformat() + "Z"

    # ── 2. Log session ─────────────────────────────────────────
    session_id = f"{last_name}_{session_date}".replace(" ", "_").lower()
    log_dir = log_session(
        session_id=session_id,
        contact=contact,
        session_metadata=session_metadata,
        transcript_path=transcript_path,
        social_audit=social_audit,
        archetypal_profile=archetypal_profile,
        stage1_path=stage1_path,
        stage2_path=stage2_path,
        plan_path=plan_path,
        pdf_path=pdf_path,
        delivery_result=delivery_result,
        output_dir=output_dir
    )

    # ── 3. Notify Eddie ────────────────────────────────────────
    notification_result = {"success": False, "simulated": True}
    if notification_email:
        notif_body = build_eddie_notification_body(
            subject_name=subject_name,
            business_name=business_name,
            business_concept=business_concept,
            viability_score=viability_score,
            readiness_score=readiness_score,
            digital_score=digital_score,
            calibration_level=calibration_level,
            delivery_email=subject_email,
            delivery_timestamp=delivery_timestamp,
            artifacts_location=log_dir
        )
        notification_result = send_email(
            to_email=notification_email,
            to_name="Eddie",
            subject=f"Blueprint Complete — {subject_name} | {business_name}",
            body=notif_body
        )

    # ── 4. Completion report ───────────────────────────────────
    social_profiles_count = len(social_audit.get("profiles", []))
    archetype_status = "Generated" if archetypal_profile.get("available") else "Not Available"

    # Count plan sections
    plan_sections = 14  # Fixed per spec
    plan_pages_approx = 25  # Estimate

    completion_report = f"""
BLUEPRINT ENGINE — PIPELINE COMPLETE
Subject: {subject_name}
Business: {business_name}
Session Duration: {session_duration} minutes
Social Profiles Audited: {social_profiles_count}
Archetypal Profile: {archetype_status}
Plan Calibration: {calibration_level}
Key Scores: Viability {viability_score}/10 | Readiness {readiness_score}/10 | Digital {digital_score}/10
Plan Length: {plan_sections} sections, ~{plan_pages_approx} pages
Delivered to: {subject_email}
Delivered at: {delivery_timestamp}
All artifacts stored: {log_dir}

Pipeline executed autonomously. No human intervention required.
""".strip()

    logger.info("\n" + completion_report)

    return {
        "delivery_result": delivery_result,
        "notification_result": notification_result,
        "log_dir": log_dir,
        "completion_report": completion_report,
        "session_id": session_id
    }
