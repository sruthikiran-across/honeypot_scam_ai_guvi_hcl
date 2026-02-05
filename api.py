import os
import traceback
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Body
from pydantic import BaseModel

from honeypot_agent import HoneypotAgent
from scammer_agent import ScammerAgent
from scam_detector import extract_entities


# ---------------- APP SETUP ----------------

app = FastAPI(title="Scam Honeypot AI")

API_KEY = os.getenv("API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")




# ---------------- HEALTH CHECK ----------------

@app.get("/")
def root():
    return {"status": "Honeypot API is running"}


# ---------------- HONEYPOT ENDPOINT (GUVI TESTER) ----------------

@app.post("/honeypot")
def honeypot_endpoint(
    request: dict | None = Body(default=None),
    x_api_key: str = Header(...)
):
    # API key validation
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Safe message handling (NO 422 possible)
    message = "test_message"
    if request and isinstance(request, dict):
        message = request.get("message", "test_message")

    honeypot = HoneypotAgent()
    entities = extract_entities(message)
    reply = honeypot.respond(message, entities)

    return {
        "status": "ok",
        "input_message": message,
        "honeypot_reply": reply["message"],
        "stage": reply["stage"],
        "confidence": reply["confidence"],
        "entities_extracted": {
            "upi": entities.get("upi_id"),
            "phone": entities.get("phone_number"),
            "links": entities.get("phishing_links")
        }
    }



# ---------------- FULL MOCK SCAM SIMULATION ----------------

@app.post("/run-mock-scam")
def run_mock_scam():
    try:
        scammer = ScammerAgent()
        honeypot = HoneypotAgent()

        conversation = []
        stage_history = []

        extracted_entities = {
            "upi": None,
            "phone": None,
            "links": []
        }

        MAX_TURNS = 8
        turn = 0

        while turn < MAX_TURNS:
            msg = scammer.generate_message(honeypot.stage)
            turn += 1

            if isinstance(msg, dict):
                msg = msg.get("message", "")

            entities = extract_entities(msg)

            if entities.get("upi_id"):
                extracted_entities["upi"] = entities["upi_id"]

            if entities.get("phone_number"):
                extracted_entities["phone"] = entities["phone_number"]

            if entities.get("phishing_links"):
                extracted_entities["links"].extend(entities["phishing_links"])

            prev_stage = honeypot.stage
            honeypot_reply = honeypot.respond(msg, entities)

            stage_history.append({
                "from_stage": prev_stage,
                "to_stage": honeypot_reply["stage"],
                "trigger_message": msg,
                "confidence": honeypot_reply["confidence"]
            })

            conversation.append({
                "from": "scammer",
                "message": msg
            })

            conversation.append({
                "from": "ai",
                "message": honeypot_reply["message"],
                "stage": honeypot_reply["stage"],
                "confidence": honeypot_reply["confidence"]
            })

            if honeypot_reply["stage"] == "controlled_exit":
                break

        return {
            "conversation": conversation,
            "final_stage": honeypot.stage,
            "stage_history": stage_history,
            "entities_extracted": extracted_entities
        }

    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}
