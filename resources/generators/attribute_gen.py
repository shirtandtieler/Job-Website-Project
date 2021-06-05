# Do not use this file directly.
# It's referenced by 'seeker_gen.py'
from typing import List

import pandas as pd
import random

df_framework = pd.read_csv("resources/generators/culture_framework.csv")
df_framework.set_index("Values", inplace=True)
values = df_framework.index.to_list()

df_skills = pd.read_csv("resources/generators/skills.csv")
biz_skills = df_skills.loc[df_skills.Type == 'Biz']['Skill'].to_list()
tech_skills = df_skills.loc[df_skills.Type == 'Tech']['Skill'].to_list()


def gen_values(k_range=(0, 10)) -> List[str]:
    """
    Generates a number of attitudes in the provided range.
    """
    k = random.randint(*k_range)
    return random.choices(values, k=k)


def gen_biz(k_range=(0, 5)) -> dict:
    """
    Generates a number of business skills in the provided range.
    Assigns a random skill 'level' between 1 and 5.
    """
    k = random.randint(*k_range)
    skills = dict()
    for s in random.choices(biz_skills, k=k):
        skills[s] = {
            "level": random.randint(1, 5)
        }
    return skills


def gen_tech(k_range=(0, 20)) -> dict:
    """
    Generates a number of business skills in the provided range.
    Assigns a random skill level between 1 and 5.
    """
    k = random.randint(*k_range)
    skills = dict()
    for s in random.choices(tech_skills, k=k):
        skills[s] = {
            "level": random.randint(1, 5)
        }
    return skills
