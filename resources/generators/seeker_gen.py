# Use this file to generate Seeker profiles, generate their attributes (skills, values),
#   and fill out a resume template.
from faker import Faker
from mailmerge import MailMerge
import barnum
import random
import re
import os

from attribute_gen import gen_values, gen_biz, gen_tech

# ATTACHING IMAGES TO DB
# https://sqlalchemy-imageattach.readthedocs.io/en/1.1.0/guide/context.html#getting-image-binary


fake = Faker()

domains = ["aol.com", "att.net", "comcast.net", "facebook.com", "gmail.com",
           "hotmail.com", "mac.com", "me.com", "mail.com", "msn.com",
           "live.com", "sbcglobal.net", "verizon.net", "yahoo.com"]
phrases = ["I'm all about {phrase}.", "What gets me out of bed is the idea of {phrase}.",
                 "I am passionate for {phrase}.",
                 "Looking for a company who appreciates {phrase} as much as I do.",
                 "Seeking a role that embraces the notion of {phrase}."]

def generate_profile(is_male) -> dict:
    profile = dict()
    if is_male:
        profile['first_name'] = fake.first_name_male()
        profile['sex'] = 'male'
    else:
        profile['first_name'] = fake.first_name_female()
        profile['sex'] = 'female'
    profile['last_name'] = fake.last_name()

    zip_code, city, state = barnum.create_city_state_zip()
    profile['city'] = city
    profile['state'] = state
    profile['zip_code'] = zip_code
    # remove non-digits from phone
    profile['phone'] = re.sub("[^\d]", "", barnum.create_phone(zip_code))

    email = barnum.create_email(name=[profile['first_name'], profile['last_name']])
    # custom overrides for email
    email = (email[:email.index("@")+1] + random.choice(domains)).lower()
    profile['email'] = email
    
    return profile

def generate_attributes() -> dict:
    attrs = dict()
    attrs["values"] = gen_values()
    attrs["skills"] = {"biz": gen_biz(), "tech": gen_tech()}
    return attrs

def make_resume(person: dict, values: list = None, skills1: list = None, skills2: list = None, output_dir: str = None):
    if values is None: values = []
    if skills1 is None: skills1 = []
    if skills2 is None: skills2 = []
    # generate description for person
    description = random.choice(phrases).format(phrase=fake.catch_phrase().lower())
    if values:
        description += " Things I value include: " + ", ".join(values)

    document = MailMerge("resume_template.docx")
    document.merge(
        first = person['first_name'],
        last = person['last_name'],
        location = person['city'] + ", " + person['state'],
        phone = f"({person['phone'][:3]}){person['phone'][3:6]}-{person['phone'][6:]}",
        email = person['email'],
        headline=description,
        skills1 = "\n".join(skills1),
        skills2 = "\n".join(skills2)
    )
    fn = f"resume_{person['first_name']}_{person['last_name']}.docx"
    if output_dir is not None:
        fn = os.path.join(output_dir, fn)
    document.write(fn)
    return fn
           
    
