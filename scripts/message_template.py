import random

def get_message():
    messages = [
        "Thanks for connecting! I build AI tools and open-source projects.\n\nWould love to stay in touch.\n\nCheers,\nHaris Ahmed",
        "Appreciate the connection! Mostly building AI and developer tools here.\n\nHappy to stay connected.\n\nBest,\nHaris Ahmed",
        "Thanks for adding me to your network.\n\nAlways great to connect with people in tech.\n\nBest regards,\nHaris Ahmed",
    ]
    return random.choice(messages)
