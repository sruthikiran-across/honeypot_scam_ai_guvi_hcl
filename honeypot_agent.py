import random
from scam_detector import generate_reply_llm


class HoneypotAgent:
    def generate_reply(self, scammer_message):
        """
        Uses LLM for human-like replies in later stages,
        falls back to rule-based replies if LLM fails.
        """
        try:
            return generate_reply_llm(
                stage=self.stage,
                scammer_message=scammer_message,
                entities=self.entities
            )
        except Exception:
            return None

    def __init__(self):
        self.stage = "low_tech_persona_establishment"
        self.confidence = 0.3
        self.entities = {
            "upi": None,
            "phone": None,
            "links": []
        }
        self.turns_in_extraction = 0
        


    def respond(self, scammer_message: str,entities:dict):
        msg = scammer_message.lower()
        if entities.get("upi_id"):
            self.entities["upi"] = entities["upi_id"]

        if entities.get("phone_number"):
            self.entities["phone"] = entities["phone_number"]

        if entities.get("phishing_links"):
            self.entities["links"].extend(entities["phishing_links"])
            llm_reply=None
            reply = None

       
        if self.has_sufficient_intel():
            self.stage = "controlled_exit"
            self.confidence = 0.9

            return {
                "from": "honeypot",
                "message": random.choice([
                    "I am not comfortable continuing this on the phone. I will visit the bank directly.",
                    "This does not feel safe. I will verify this at the bank branch.",
                    "Please do not call me again. I will check directly with the bank."
                ]),
                "stage": self.stage,
                "confidence": self.confidence
            }

        
       # -------- STAGE 1: LOW TECH --------
        if self.stage == "low_tech_persona_establishment":

            llm_reply = generate_reply_llm(
                stage=self.stage,
                scammer_message=scammer_message,
                entities={}
            )

            reply = llm_reply or random.choice([
                "I dont know much about phone sir, my son does everything.",
                "This mobile only for calling, I get confused.",
                "What is this message? I am scared."
            ])

            if "bank" in msg or "account" in msg:
                self.stage = "skepticism_trigger"
                self.confidence = 0.4


# -------- STAGE 2: SKEPTICISM --------
        elif self.stage == "skepticism_trigger":

            reply = random.choice([
                "My son told me banks never call like this. Why are you calling me?",
                "I have heard about many fraud calls. How do I know this is genuine?",
                "If this is from the bank, why didn’t they ask me to visit the branch?"
            ])

            if any(k in msg for k in ["verify", "security", "suspension", "link", "send", "@"]):
                self.stage = "guided_action_engagement"
                self.confidence = 0.5




# -------- STAGE 3: GUIDED ACTION --------
        elif self.stage == "guided_action_engagement":

            reply = random.choice([
                "If this is from the bank, why didn’t they ask me to visit the branch?",
                "Why should this be done urgently?",
                "Why is this verification happening on phone?"
            ])

            if self.has_sufficient_intel():
                self.stage = "controlled_exit"
                self.confidence = 0.85

               
                reply = random.choice([
                    "I am not comfortable continuing this on the phone. I will visit the bank directly.",
                    "My son will handle this matter. Please do not call me again.",
                    "I will confirm this at the bank branch. I am ending the call now."
                ])



           


# -------- STAGE 4: EXTRACTION --------
        elif self.stage == "entity_confirmation_and_extraction":

            if self.entities["phone"]:
                reply = f"You said the number is {self.entities['phone']}, correct?"

            elif self.entities["upi"]:
                reply = f"You want me to send money to {self.entities['upi']}, right?"

            elif self.entities["links"]:
                reply = "You sent me a link just now. Why do I need to open it?"

            else:
                llm_reply = generate_reply_llm(
                    stage=self.stage,
                    scammer_message=scammer_message,
                    entities=entities
                )
                reply = llm_reply or random.choice([
                    "Please repeat the details slowly so I can note them.",
                    "What exactly should I write down?"
                ])




      
      # -------- STAGE 5: CONTROLLED EXIT (FINAL POLISH) --------
        elif self.stage == "controlled_exit":

            reply = random.choice([
                "I am not comfortable continuing this on the phone. I will visit the bank directly.",
                "My son will handle this matter. Please do not call me again.",
                "I will confirm this at the bank branch. I am ending the call now."
            ])

            self.confidence = 0.9




           
        return {
            "from": "honeypot",
            "message": reply,
            "stage": self.stage,
            "confidence": self.confidence
        }
    def has_sufficient_intel(self):
        return (
            self.entities.get("upi") is not None
            or self.entities.get("phone") is not None
            or len(self.entities.get("links", [])) > 0
        )

    
