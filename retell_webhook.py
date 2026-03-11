#!/usr/bin/env python3
"""
BLUEPRINT ENGINE — Retell AI Native Webhook Handler
Exsuvera LLC / Lion Ass Bitch (LAB)

This server receives the `call_analyzed` webhook directly from Retell AI
after a Blueprint Session (or intake questionnaire call) ends.

Retell sends three events per call:
  1. call_started   — ignored
  2. call_ended     — ignored (transcript may not be final)
  3. call_analyzed  — THIS is what we act on (full transcript + analysis fields)

The handler:
  1. Validates the event type (only processes call_analyzed)
  2. Extracts the full transcript from call.transcript
  3. Reads structured fields from call.call_analysis (if Post-Call Analysis is configured)
  4. Builds the pipeline payload
  5. Fires the full Blueprint Engine pipeline asynchronously

─────────────────────────────────────────────────────────────────
RETELL SETUP (one-time, in your Retell dashboard):
─────────────────────────────────────────────────────────────────
1. Go to Dashboard → Your Agent → Post-Call Analysis
2. Add these custom analysis fields (type: Text unless noted):

   Field name          Type    Description
   ──────────────────  ──────  ─────────────────────────────────────────────────
   first_name          Text    "The caller's first name"
   last_name           Text    "The caller's last name"
   email               Text    "The caller's email address"
   phone               Text    "The caller's phone number"
   location            Text    "The caller's city and state"
   birthday            Text    "The caller's date of birth in YYYY-MM-DD format"
   birth_time          Text    "The caller's time of birth (HH:MM). If unknown, return null"
   birth_location      Text    "The city/country where the caller was born. If unknown, return null"
   website             Text    "The caller's business website URL. If none, return null"
   instagram           Text    "The caller's Instagram handle without @. If none, return null"
   youtube             Text    "The caller's YouTube channel handle without @. If none, return null"
   facebook            Text    "The caller's Facebook page name or URL. If none, return null"
   linkedin            Text    "The caller's LinkedIn profile URL. If none, return null"
   tiktok              Text    "The caller's TikTok handle without @. If none, return null"

3. Go to Dashboard → Your Agent → Webhook
4. Set webhook URL to: https://your-server.com/retell-webhook
5. Select event: call_analyzed (only)

─────────────────────────────────────────────────────────────────
FALLBACK (if Post-Call Analysis is not configured):
─────────────────────────────────────────────────────────────────
If call_analysis fields are missing, the handler falls back to
Claude-based extraction from the raw transcript text.
This is slower (~30s) but requires zero Retell configuration.
─────────────────────────────────────────────────────────────────
"""

import argparse
import hashlib
import hmac
import json
import logging
import os
import sys
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(__file__))
from orchestrator import run_pipeline, setup_logging
from modules.retell_payload_mapper import map_retell_to_pipeline_payload

logger = logging.getLogger("RetellWebhook")


class RetellWebhookHandler(BaseHTTPRequestHandler):
    output_dir = "/home/ubuntu/blueprint_engine/output"
    retell_api_key = None  # Set via env var RETELL_API_KEY for signature verification

    # ── Routing ──────────────────────────────────────────────
    def do_POST(self):
        if self.path not in ("/retell-webhook", "/retell-webhook/"):
            self._send_json(404, {"error": "Not found"})
            return
        self._handle_retell_event()

    def do_GET(self):
        if self.path in ("/", "") or self.path == "/health":
            self._send_json(200, {
                "status": "healthy",
                "service": "Blueprint Engine — Retell Webhook",
                "company": "Exsuvera LLC / LAB",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        else:
            self._send_json(404, {"error": "Not found"})

    # ── Main handler ─────────────────────────────────────────
    def _handle_retell_event(self):
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)

        # Optional: verify Retell signature
        if self.retell_api_key:
            if not self._verify_signature(raw_body):
                logger.warning("Webhook signature verification failed.")
                self._send_json(401, {"error": "Invalid signature"})
                return

        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError as e:
            self._send_json(400, {"error": f"Invalid JSON: {e}"})
            return

        event_type = data.get("event") or data.get("event_type", "")

        # Only process call_analyzed — ignore call_started and call_ended
        if event_type != "call_analyzed":
            logger.info(f"Ignoring event: {event_type}")
            self._send_json(200, {"status": "ignored", "event": event_type})
            return

        call = data.get("call", {})
        call_id = call.get("call_id", "unknown")
        transcript = call.get("transcript", "")

        if not transcript or len(transcript.strip()) < 50:
            logger.warning(f"Call {call_id}: transcript too short or missing.")
            self._send_json(400, {"error": "Transcript missing or too short to process"})
            return

        # Acknowledge immediately — pipeline runs async
        self._send_json(202, {
            "status": "accepted",
            "call_id": call_id,
            "message": "Blueprint Engine pipeline started. Plan will be delivered via email."
        })

        # Fire pipeline in background thread
        thread = threading.Thread(
            target=self._run_pipeline_async,
            args=(call, transcript),
            daemon=True
        )
        thread.start()

    def _run_pipeline_async(self, call: dict, transcript: str):
        """Map Retell call object → pipeline payload, then run the pipeline."""
        call_id = call.get("call_id", "unknown")
        logger.info(f"Building pipeline payload for call {call_id}...")

        try:
            payload = map_retell_to_pipeline_payload(call, transcript)
        except Exception as e:
            logger.error(f"Payload mapping failed for call {call_id}: {e}")
            return

        first_name = payload.get("contact", {}).get("first_name", "unknown")
        last_name = payload.get("contact", {}).get("last_name", "unknown")
        session_date = payload.get("session_metadata", {}).get(
            "session_date", datetime.utcnow().strftime("%Y-%m-%d")
        )

        session_output_dir = os.path.join(
            self.output_dir,
            f"{last_name}_{session_date}_{datetime.utcnow().strftime('%H%M%S')}"
        )

        logger.info(f"Starting pipeline for {first_name} {last_name} (call {call_id})...")
        try:
            run_pipeline(
                payload=payload,
                transcript=transcript,
                output_dir=session_output_dir
            )
            logger.info(f"Pipeline complete for {first_name} {last_name}.")
        except Exception as e:
            logger.error(f"Pipeline failed for {first_name} {last_name}: {e}")

    # ── Signature verification ────────────────────────────────
    def _verify_signature(self, raw_body: bytes) -> bool:
        """
        Retell signs webhooks with HMAC-SHA256 using your API key.
        Header: x-retell-signature
        """
        signature = self.headers.get("x-retell-signature", "")
        if not signature:
            return False
        expected = hmac.new(
            self.retell_api_key.encode(),
            raw_body,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected)

    # ── Helpers ───────────────────────────────────────────────
    def _send_json(self, status: int, body: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def log_message(self, format, *args):
        logger.info(f"{self.address_string()} - {format % args}")


def main():
    parser = argparse.ArgumentParser(description="Blueprint Engine — Retell AI Webhook Server")
    parser.add_argument("--port", type=int,
                        default=int(os.environ.get("PORT", 8080)),
                        help="Port to listen on (overridden by PORT env var)")
    parser.add_argument("--output-dir",
                        default=os.environ.get("OUTPUT_DIR", "/tmp/sessions"),
                        help="Output directory for pipeline artifacts")
    args = parser.parse_args()

    setup_logging(args.output_dir)
    RetellWebhookHandler.output_dir = args.output_dir
    RetellWebhookHandler.retell_api_key = os.environ.get("RETELL_API_KEY")

    server = HTTPServer(("0.0.0.0", args.port), RetellWebhookHandler)
    logger.info(f"Retell Webhook Server running on port {args.port}")
    logger.info(f"POST endpoint: http://0.0.0.0:{args.port}/retell-webhook")
    logger.info(f"Health check:  http://0.0.0.0:{args.port}/health")
    if not RetellWebhookHandler.retell_api_key:
        logger.warning("RETELL_API_KEY not set — webhook signature verification disabled.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped.")


if __name__ == "__main__":
    main()
