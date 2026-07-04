import random

def get_welcome_message(name=""):
    greeting = "Hi" if not name else f"Hi {name}"
    messages = [
        f"{greeting},\n\nThanks for connecting! I build AI tools, APIs, and open-source projects on GitHub. Always happy to connect with people who share an interest in tech.\n\nLooking forward to seeing what you're working on.\n\nCheers,\nHaris Ahmed",
        f"{greeting},\n\nAppreciate the connection! I work on developer tools and AI projects — mostly open-source. Always open to interesting discussions around tech, product, and building in public.\n\nLet's stay in touch.\n\nBest,\nHaris Ahmed",
        f"{greeting},\n\nThanks for adding me to your network. I'm a developer focused on AI, APIs, and open-source — always exploring new ideas in the space.\n\nHappy to connect and share insights.\n\nBest regards,\nHaris Ahmed",
    ]
    return random.choice(messages)
