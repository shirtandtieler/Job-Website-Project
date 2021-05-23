# Use this file to generate job posts for a given company's profile.

import json
import random
from faker import Faker

fake = Faker()

with open("job_dataset.json") as f:
    dataset = json.load(f)


titles, weights = [], []
for title, info in dataset.items():
    titles.append(title)
    weights.append(info['jobs'])

def generate_jobpost(company: dict):
    post = dict()
    
    title = random.choices(titles, weights)[0]
    post["title"] = title

    # Start description
    desc = f"{company['name']} is looking for someone to fill the role of {title}.\n"
    
    info = dataset[title]
    # Add income information
    desc += "Income: "
    if random.random() < 0.75:
        rng = info["range"]
        if random.random() < 0.3:
            desc += f"Up to {info['range'][1]}\n"
        elif random.random() < 0.3:
            desc += f"{info['range'][0]}+\n"
        else:
            desc += str(info['range']) + "\n"
    else:
        desc += "Depends on experience.\n"

    post["description"] = desc
    post["creation"] = fake.date_time_this_year()
    post["active"] = random.random() > 0.05

    return post
    
