import traceback
import json
from honeypot_agent import HoneypotAgent
from datetime import datetime
from fastapi import FastAPI
from scam_detector import extract_entities


app = FastAPI(title="Scam Honeypot AI")

from scammer_agent import ScammerAgent



# ---------------- FULL SIMULATION ENDPOINT ----------------

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
            # ---- SCAMMER SPEAKS ----
            msg = scammer.generate_message(honeypot.stage)
            turn += 1

            if isinstance(msg, dict):
                msg = msg.get("message", "")

            print(" SCAMMER:", msg)

            entities = extract_entities(msg)
            print(" ENTITIES:", entities)

            if entities.get("upi_id"):
                extracted_entities["upi"] = entities["upi_id"]

            if entities.get("phone_number"):
                extracted_entities["phone"] = entities["phone_number"]

            if entities.get("phishing_links"):
                extracted_entities["links"].extend(entities["phishing_links"])

            # ---- HONEYPOT RESPONDS ----
            prev_stage = honeypot.stage
            honeypot_reply = honeypot.respond(msg, entities)

            print(" HONEYPOT:", honeypot_reply)

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

        exit_reason = None
        if honeypot.stage == "controlled_exit":
                exit_reason = "sufficient_intel_collected"

        return {
                "conversation": conversation,
                "final_stage": honeypot.stage,
                "exit_reason": exit_reason,  
                "stage_history": stage_history,
                "entities_extracted": extracted_entities
            }

    except Exception as e:
        print(" ENDPOINT CRASHED")
        traceback.print_exc()
        return {"error": str(e)}
from fastapi import Header, HTTPException
from pydantic import BaseModel

import os

API_KEY = os.getenv("API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
 

from typing import Optional

class HoneypotRequest(BaseModel):
    message: str | None = None



@app.get("/")
def root():
    return {"status": "Honeypot API is running"}


from fastapi import Body

@app.post("/honeypot")
def honeypot_endpoint(
    request: HoneypotRequest = Body(default=None),
    x_api_key: str = Header(...)
):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    message = request.message if request and request.message else "test_message"

    return {
        "status": "ok",
        "message": message
    }

    # 2. Create honeypot agent
    honeypot = HoneypotAgent()

    # 3. Extract entities from incoming message
    entities = extract_entities(request.message)

    # 4. Get honeypot response
    reply = honeypot.respond(request.message, entities)

    # 5. Return clean JSON
    return {
        "input_message": request.message,
        "honeypot_reply": reply["message"],
        "stage": reply["stage"],
        "confidence": reply["confidence"],
        "entities_extracted": {
            "upi": entities.get("upi_id"),
            "phone": entities.get("phone_number"),
            "links": entities.get("phishing_links")
        }
    }

