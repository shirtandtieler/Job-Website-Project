# Do not use this file directly.
# It's referenced by 'seeker_gen.py'

import pandas as pd
import random

df_framework = pd.read_csv("culture_framework.csv")
df_framework.set_index("Values", inplace=True)
values = df_framework.index.to_list()

df_skills = pd.read_csv("skills.csv")
biz_skills = df_skills.loc[df_skills.Type=='Biz']['Skill'].to_list()
tech_skills = df_skills.loc[df_skills.Type=='Tech']['Skill'].to_list()

def gen_values(k_range=(0,10)):
    k = random.randint(*k_range)
    return random.choices(values, k=k)

def gen_biz(k_range=(0,5)):
    k = random.randint(*k_range)
    return random.choices(biz_skills, k=k)

def gen_tech(k_range=(0,20)):
    k = random.randint(*k_range)
    return random.choices(tech_skills, k=k)
