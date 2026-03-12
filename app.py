#!/usr/bin/env python3
"""
Blueprint Engine - Minimal Render-compatible webhook server
"""
import json
import logging
import os
import sys
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("BlueprintEngine")

PORT = int(os.environ.get("PORT", 8080))
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/tmp/sessions")
os.makedirs(OUTPUT_DIR, exist_ok=True)


class WebhookHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self._send_json(200, {
            "status": "healthy",
            "service": "Blueprint Engine - Retell Webhook",
            "company": "Exsuvera LLC / LAB",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        path = self.path.rstrip("/")
        if path == "/text-intake":
            self._handle_text_intake()
            return
        if path not in ("/retell-webhook",):
            self._send_json(404, {"error": "Not found"})
            return

        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)

        try:
            data = json.loads(raw_body)
        except Exception as e:
            self._send_json(400, {"error": f"Invalid JSON: {e}"})
            return

        event_type = data.get("event", data.get("event_type", ""))
        if event_type != "call_analyzed":
            logger.info(f"Ignoring event: {event_type}")
            self._send_json(200, {"status": "ignored", "event": event_type})
            return

        call = data.get("call", {})
        call_id = call.get("call_id", "unknown")
        transcript = call.get("transcript", "")

        if not transcript or len(transcript.strip()) < 50:
            self._send_json(400, {"error": "Transcript too short"})
            return

        self._send_json(202, {
            "status": "accepted",
            "call_id": call_id,
            "message": "Blueprint Engine pipeline started. Plan will be delivered via email."
        })

        thread = threading.Thread(
            target=self._run_pipeline,
            args=(call, transcript),
            daemon=True
        )
        thread.start()

    def _run_pipeline(self, call, transcript):
        call_id = call.get("call_id", "unknown")
        logger.info(f"Starting pipeline for call {call_id}")
        try:
            sys.path.insert(0, os.path.dirname(__file__))
            from modules.retell_payload_mapper import map_retell_to_pipeline_payload
            from orchestrator import run_pipeline
            payload = map_retell_to_pipeline_payload(call, transcript)
            first = payload.get("contact", {}).get("first_name", "unknown")
            last = payload.get("contact", {}).get("last_name", "unknown")
            session_dir = os.path.join(OUTPUT_DIR, f"{last}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
            run_pipeline(payload=payload, transcript=transcript, output_dir=session_dir)
            logger.info(f"Pipeline complete for {first} {last}")
        except Exception as e:
            logger.error(f"Pipeline failed for call {call_id}: {e}", exc_info=True)

    def _handle_text_intake(self):
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)
        try:
            data = json.loads(raw_body)
        except Exception as e:
            self._send_json(400, {"error": f"Invalid JSON: {e}"})
            return

        email = data.get("subject", {}).get("email", "")
        if not email:
            self._send_json(400, {"error": "Email is required"})
            return

        self._send_json(202, {
            "status": "accepted",
            "message": "Blueprint Engine pipeline started. Your plan will be delivered via email."
        })

        thread = threading.Thread(
            target=self._run_text_pipeline,
            args=(data,),
            daemon=True
        )
        thread.start()

    def _run_text_pipeline(self, form_data):
        email = form_data.get("subject", {}).get("email", "unknown")
        logger.info(f"Starting text intake pipeline for {email}")
        try:
            sys.path.insert(0, os.path.dirname(__file__))
            from orchestrator import run_pipeline
            # Build transcript from form data for the pipeline
            subject = form_data.get("subject", {})
            business = form_data.get("business", {})
            background = form_data.get("background", {})
            psychology = form_data.get("psychology", {})
            digital = form_data.get("digital", {})
            ops = form_data.get("operations", {})

            transcript_parts = [
                f"Name: {subject.get('first_name', '')} {subject.get('last_name', '')}",
                f"Email: {subject.get('email', '')}",
                f"Location: {subject.get('location', '')}",
                f"Birthday: {subject.get('birthday', '')}",
                f"Background: {background.get('professional', '')}",
                f"Known for: {background.get('known_for', '')}",
                f"Business idea: {business.get('idea', '')}",
                f"Target customer: {business.get('target_customer', '')}",
                f"3-year vision: {business.get('three_year_vision', '')}",
                f"Why me: {business.get('why_you', '')}",
                f"Revenue model: {business.get('revenue_model', '')}",
                f"Pricing: {business.get('pricing', '')}",
                f"Competitors: {business.get('competitors', '')}",
                f"Differentiator: {business.get('differentiator', '')}",
                f"Instagram: {digital.get('instagram', '')}",
                f"Website: {digital.get('website', '')}",
                f"Biggest fear: {psychology.get('biggest_fear', '')}",
                f"Avoidance: {psychology.get('avoidance', '')}",
                f"Hours per week: {ops.get('hours_per_week', '')}",
            ]
            synthetic_transcript = "\n".join(t for t in transcript_parts if t.split(": ", 1)[-1].strip())

            # Build pipeline payload
            payload = {
                "contact": {
                    "first_name": subject.get("first_name", ""),
                    "last_name": subject.get("last_name", ""),
                    "email": subject.get("email", ""),
                    "phone": subject.get("phone", ""),
                    "location": subject.get("location", ""),
                    "birthday": subject.get("birthday", ""),
                    "birth_time": subject.get("birth_time"),
                    "birth_location": subject.get("birth_location"),
                    "website": digital.get("website"),
                    "instagram": digital.get("instagram"),
                    "youtube": digital.get("youtube"),
                    "facebook": None,
                    "linkedin": None,
                    "tiktok": digital.get("tiktok"),
                },
                "source": "text_questionnaire",
            }

            first = subject.get("first_name", "unknown")
            last_name = subject.get("last_name", "unknown")
            session_dir = os.path.join(OUTPUT_DIR, f"{last_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
            run_pipeline(payload=payload, transcript=synthetic_transcript, output_dir=session_dir)
            logger.info(f"Text intake pipeline complete for {first} {last_name}")
        except Exception as e:
            logger.error(f"Text intake pipeline failed for {email}: {e}", exc_info=True)

    def _send_json(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def log_message(self, fmt, *args):
        logger.info(f"{self.address_string()} - {fmt % args}")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), WebhookHandler)
    logger.info(f"Blueprint Engine running on port {PORT}")
    logger.info(f"Health: http://0.0.0.0:{PORT}/")
    logger.info(f"Webhook: http://0.0.0.0:{PORT}/retell-webhook")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped.")
