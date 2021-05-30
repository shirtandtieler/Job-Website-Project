
with open("resources/generators/skills.csv") as f:
    SKILL_NAMES = [s.split(",")[0] for s in f.read().split("\n")[1:] if s]


with open("resources/generators/culture_framework.csv") as f:
    ATTITUDE_NAMES = [s.split(",")[0] for s in f.read().split("\n")[1:] if s]