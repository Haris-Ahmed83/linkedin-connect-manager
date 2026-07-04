import random

SENDER_NAME = "Muhammad Haris"

def generate_message(name, headline=""):
    headline_lower = (headline or "").lower()

    if any(kw in headline_lower for kw in ["ai", "machine learning", "llm", "gpt", "data", "artificial"]):
        # AI/data person
        body = random.choice([
            f"Thanks for connecting, {name}! I've been following the AI space closely and love seeing others working in this field. I mostly build AI tools and APIs myself.\n\nAlways great to stay in touch.\n\nBest,\n{SENDER_NAME}",
            f"Great to connect, {name}! I see you're working in the AI space — I've been building AI tools and APIs myself. Always exciting to meet others exploring this field.\n\nLooking forward to staying connected.\n\nBest regards,\n{SENDER_NAME}",
        ])

    elif any(kw in headline_lower for kw in ["ceo", "founder", "co-founder", "cto", "startup", "entrepreneur"]):
        # Founder/CEO
        body = random.choice([
            f"Thanks for connecting, {name}! I'm always interested in connecting with founders and entrepreneurs. I build tech products and open-source tools.\n\nHappy to stay in touch.\n\nBest,\n{SENDER_NAME}",
            f"Appreciate the connection, {name}! Love meeting people who are building things. I work on developer tools and AI projects — always open to collaborating or exchanging ideas.\n\nBest regards,\n{SENDER_NAME}",
        ])

    elif any(kw in headline_lower for kw in ["developer", "engineer", "software", "programmer", "dev", "full stack", "backend", "frontend"]):
        # Developer
        body = random.choice([
            f"Thanks for connecting, {name}! Great to connect with a fellow developer. I build open-source projects and AI tools — always happy to share notes.\n\nLet's stay in touch.\n\nBest,\n{SENDER_NAME}",
            f"Appreciate the connection, {name}! Always great to meet other devs building in the space. I work on AI APIs and developer tools.\n\nLooking forward to seeing what you're working on.\n\nCheers,\n{SENDER_NAME}",
        ])

    else:
        # General
        body = random.choice([
            f"Thanks for connecting, {name}! I build AI tools and open-source projects. Always great to connect with people who share an interest in tech.\n\nLet's stay in touch.\n\nBest,\n{SENDER_NAME}",
            f"Appreciate the connection, {name}! I'm a developer focused on AI, APIs, and open-source projects. Happy to stay connected.\n\nBest regards,\n{SENDER_NAME}",
        ])

    return body

def get_message(name="", headline=""):
    return generate_message(name, headline)
