import random

class ScammerAgent:
    def __init__(self):
        self.turn = 0
        self.last_tactic = None

        self.tactics = {
            "opening": [
                "Hello, I am calling from your bank regarding a suspicious transaction.",
                "Namaste madam, this is bank customer care calling about your account."
            ],
            "authority": [
                "I am calling from the bank verification department.",
                "This is official customer care."
            ],
            "payload": [
                "Please send ₹1 to raj@okhdfc to verify your account.",
                "You can also call our verification desk at 9876543210.",
                "Click this link to complete verification: http://fakebank.in/verify"
            ],
            "urgency": [
                "You must act within 10 minutes.",
                "Delay will result in account suspension."
            ],
            "final_escalation": [
                "This is your final warning. Your account will be blocked."
            ]
        }

    def decide_next_tactic(self, victim_stage):
        if self.turn == 1:
            return "opening"

        if self.turn == 2:
            return "authority"

        if self.turn in [3, 4]:
            return "payload"

        if victim_stage == "entity_confirmation_and_extraction":
            return "payload"

        if victim_stage == "skepticism_trigger":
            return random.choice(["urgency","payload"]) 

        return "final_escalation"

    def soften(self, message):
        prefixes = [
            "Please don't worry madam.",
            "I will help you, madam.",
            "Kindly listen carefully madam.",
            ""
        ]
        return f"{random.choice(prefixes)} {message}".strip()

    def generate_message(self, victim_stage):
        self.turn += 1

        tactic = self.decide_next_tactic(victim_stage)

        if tactic == self.last_tactic:
            tactic = "urgency"

        self.last_tactic = tactic

        return {
    "from": "scammer",
    "tactic": tactic,
    "message": self.soften(random.choice(self.tactics[tactic]))
}

