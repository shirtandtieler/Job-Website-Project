# Use this file to generate a company profile.
# Also contains a culture archetype to later use in reference to their jobs' values (for tyler TODO)

import barnum
import random
import re
from faker import Faker

fake = Faker()

with open("companies.csv") as f:
    companies = f.read().split("\n")

with open("culture_framework.csv") as f:
    archetypes = f.readline().split(",")[1:]

enames = ["recruiter", "hr", "info", "job", "inquiry"]

def generate_profile():
    profile = dict()
    name = random.choice(companies)
    profile['name'] = name
    email = random.choice(enames) + "@" + re.sub("[^\w]", "", name).lower() + "." + fake.tld()
    profile['email'] = email
    
    zip_code, city, state = barnum.create_city_state_zip()
    profile['city'] = city
    profile['state'] = state
    profile['zip_code'] = zip_code

    profile['archetype'] = random.choice(archetypes)
    return profile
