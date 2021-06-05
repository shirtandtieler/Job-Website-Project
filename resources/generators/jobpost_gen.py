# Use this file to generate job posts for a given company's profile.

import json
import random
from faker import Faker

fake = Faker()

with open("resources/generators/job_dataset.json") as f:
    dataset = json.load(f)

with open("resources/generators/culture_framework.csv") as f:
    attitudes = [x.split(",", 1)[0] for x in f.read().split("\n")[1:] if x]

titles, weights = [], []
for title, info in dataset.items():
    titles.append(title)
    weights.append(info['jobs'])


def generate_jobpost(company_name, city=None, state=None, website=None):
    """
    Generates dict with keys:
        title: str
        description: str
        salary: {min: #/None, max: #/None}
        skills: {name: {importance:#, experience:#}}
        attitudes: {name: {importance:#}}
        remote: boolean
        creation: datetime
        active: boolean
        location: {city:X, state:X}
    """
    post = dict()

    title = random.choices(titles, weights)[0]
    info = dataset[title]  # job info from the dataset

    post["title"] = title

    # Start description
    desc = f"{company_name} is looking for someone to fill the role of {title}.\n"
    # Add income information
    desc += "Income: "
    if random.random() < 0.75:
        lwr, upr = info["range"]
        if random.random() < 0.3:  # just upper bound
            desc += f"Up to {upr}\n"
            post["salary"] = {"min": None, "max": upr}
        elif random.random() < 0.3:  # just lower bound
            desc += f"{lwr}+\n"
            post["salary"] = {"min": lwr, "max": None}
        else:  # full range
            desc += str(info['range']) + "\n"
            post["salary"] = {"min": lwr, "max": upr}
    else:
        desc += "Depends on experience.\n"
        post["salary"] = {"min": None, "max": None}
    if website is not None:
        desc += f"\nRead more about us on our website: {website}"
    post["description"] = desc

    # add generated skill info
    _skills = random.choices(info["skills"], k=random.randint(4, 8))
    top_skills = random.choices(_skills, k=random.randint(1, 3))
    opt_skills = set(_skills).difference(set(top_skills))
    post["skills"] = dict()
    for s in top_skills:  # top skills are high experience, high importance
        post["skills"][s] = {
            "experience": random.randint(4, 5),
            "importance": random.randint(3, 5)
        }
    for s in opt_skills:  # optional skills are any experience, lowish importance
        post["skills"][s] = {
            "experience": random.randint(1, 5),
            "importance": random.randint(1, 3)
        }

    # add generate attitudes
    post["attitudes"] = dict()
    for a in random.choices(attitudes, k=random.randint(5, 10)):
        post["attitudes"][a] = {
            "importance": random.randint(2, 5)
        }

    post["remote"] = random.random() < 0.3
    post["creation"] = fake.date_time_this_year()
    post["active"] = random.random() > 0.05
    if city or state:
        post["location"] = {"city": city, "state": state}

    return post
