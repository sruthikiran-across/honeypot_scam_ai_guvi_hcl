import re
import random
import os
from google import genai
conversation_log = []


# ---------------- GEMINI CLIENT ----------------


def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in environment")
    return genai.Client(api_key=api_key)



# ---------------- STAGES ----------------

STAGE_LOW_TECH = "low_tech_persona_establishment"
STAGE_SKEPTICISM = "skepticism_trigger"
STAGE_GUIDED = "guided_action_engagement"
STAGE_EXTRACTION = "entity_confirmation_and_extraction"
STAGE_EXIT = "controlled_exit"

STAGE_INSTRUCTIONS = {
    STAGE_LOW_TECH:
        "Act confused about smartphones.",

    STAGE_SKEPTICISM:
        "Be doubtful but polite. Mention scam warnings without accusing.",

    STAGE_GUIDED:
        "Ask the other person to explain steps slowly.",

    STAGE_EXTRACTION:
        "Repeat important details carefully to confirm them.",

    STAGE_EXIT:
        "End the conversation politely with a believable excuse."
}

# ---------------- REGEX ----------------

UPI_REGEX = r"[a-zA-Z0-9._-]+@[a-zA-Z]+"
PHONE_REGEX = r"\+91[6-9][0-9]{9}|[6-9][0-9]{9}"
URL_REGEX = r"https?://\S+"

# ---------------- KEYWORDS ----------------

URGENCY_KEYWORDS = ["urgent", "immediately", "now", "blocked", "suspended"]
AUTHORITY_KEYWORDS = ["bank", "police", "kyc", "account", "verification"]
PAYMENT_KEYWORDS = ["pay", "payment", "upi", "gpay", "phonepe", "send money"]

PERSUASION_KEYWORDS = [
    "trust", "official", "secure", "verified",
    "safe", "authorized", "confirmed"
]

# ---------------- HELPERS ----------------

def contains_keyword(message, keywords):
    if not message:
        return False
    msg = message.lower()
    return any(k in msg for k in keywords)

def detect_scam(message):
    urgency = contains_keyword(message, URGENCY_KEYWORDS)
    authority = contains_keyword(message, AUTHORITY_KEYWORDS)
    payment = contains_keyword(message, PAYMENT_KEYWORDS)
    score = sum([urgency, authority, payment])

    return score >= 2

def extract_entities(message):
    return {
        "upi_id": re.findall(UPI_REGEX, message)[0] if re.findall(UPI_REGEX, message) else None,
        "phone_number": re.findall(PHONE_REGEX, message)[0] if re.findall(PHONE_REGEX, message) else None,
        "phishing_links": re.findall(URL_REGEX, message)
    }

def has_any_entity(entities):
    return any([
        entities.get("upi_id"),
        entities.get("phone_number"),
        entities.get("phishing_links")
    ])

def persuasion_detected(message):
    return contains_keyword(message, PERSUASION_KEYWORDS)

# ---------------- STAGE TRANSITION ----------------

def get_next_stage(current_stage, message, entities):

    if current_stage == STAGE_LOW_TECH:
        if detect_scam(message):
            return STAGE_SKEPTICISM
        return STAGE_LOW_TECH

    if current_stage == STAGE_SKEPTICISM:
        if persuasion_detected(message):
            return STAGE_GUIDED
        return STAGE_SKEPTICISM

    if current_stage == STAGE_GUIDED:
      return STAGE_EXTRACTION


    if current_stage == STAGE_EXTRACTION:
        return STAGE_EXIT

    return STAGE_EXIT
#--------making it realistic----------
def introduce_typos(text, probability=0.2):
    """
    Introduce small human-like typos with low probability.
    """
    if random.random() > probability:
        return text

    typo_map = {
        "you": "u",
        "your": "ur",
        "please": "pls",
        "okay": "ok",
        "because": "becoz",
        "understand": "undrstand",
        "message": "mesage",
        "number": "nmbr"
    }

    words = text.split()
    for i in range(len(words)):
        if words[i].lower() in typo_map and random.random() < 0.3:
            words[i] = typo_map[words[i].lower()]

    return " ".join(words)
def add_hesitation(text, stage):
    hesitation_prefixes = {
        STAGE_LOW_TECH: ["umm", "hmm", ""],
        STAGE_SKEPTICISM: ["are you sure", "i dont know", ""],
        STAGE_GUIDED: ["ok wait", "one minute", ""],
        STAGE_EXTRACTION: ["just confirming", ""],
        STAGE_EXIT: ["sorry", "cant talk now", ""]
    }

    prefix = random.choice(hesitation_prefixes.get(stage, [""]))
    if prefix:
        return f"{prefix} {text}"
    return text



# ---------------- GEMINI REPLY ----------------



def generate_reply_llm(stage, scammer_message, entities):
   prompt = f"""
You are a middle-aged Indian woman with low digital literacy.
You are cautious, polite, and safety-aware.

Current stage: {stage}

Stage-specific rules:
- If stage is skepticism_trigger:
  Do NOT say "I don't understand".
  Express doubt or suspicion.
  Question why the call is happening.

- If stage is guided_action_engagement:
  Do NOT say "I don't understand".
  Ask what action is being requested.
  Ask why it must be urgent.

- If stage is controlled_exit:
  Do NOT ask questions.
  Clearly refuse to continue.
  End the conversation safely.

Last message from caller:
"{scammer_message}"

Reply with ONE short sentence that follows the rules.
"""


   try:
        client = get_gemini_client()
        response = client.models.generate_content(
            model="models/gemini-flash-latest",
            contents=prompt
        )
        text = response.text.strip()

   except Exception as e:
        print("GEMINI ERROR:", e)
        text = "I am not understanding properly, can you explain slowly?"

    # post-processing ALWAYS runs
        text = add_hesitation(text, stage)
        text = introduce_typos(text)

        return text









    










