import random
from datetime import datetime


def random_number(low=1, high=100, decimals=0):
    if decimals == 0:
        return str(random.randint(low, high))
    return str(round(random.uniform(low, high), decimals))


def random_time_string():
    hour = random.randint(0, 23)
    minute = random.choice([0, 15, 30, 45])
    return f"{hour:02d}:{minute:02d}"


def today_str(fmt="%d %b %Y"):
    return datetime.now().strftime(fmt)
