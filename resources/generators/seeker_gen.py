# Use this file to generate Seeker profiles, generate their attributes (skills, values),
#   and fill out a resume template.
import json
import random
import re
from operator import itemgetter
from typing import Tuple, List

# from mailmerge import MailMerge
import barnum
from faker import Faker

from app.models import SeekerProfile
from resources.generators.attribute_gen import gen_values, gen_biz, gen_tech

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
school_templates = [
    "{state} Institute of Technology",
    "University of {state}",
    "{first}town {schooltype}",
    "{last} {schooltype}",
    "{company} {schooltype}"
]
degrees = ["Computer Science", "Computing", "Cybersecurity", "Data Science",
           "Industrial Design", "Information Systems", "Information Technology", "Computer engineering",
           "Network Engineering and Security"]
adjectives = ["Adaptable", "Flexible", "Agile", "Multifaceted", "Capable", "Resourceful", "Coherent", "Harmonious",
              "Personable", "Conscientious", "Cooperative", "Charming", "Positive", "Cheerful", "Courteous",
              "Respectful", "Diplomatic", "Team-minded", "Professional", "Punctual", "Dependable", "Honest", "Diligent",
              "Steadfast", "Disciplined", "Loyal", "Methodical", "Detailed", "Detail-oriented", "Enterprising",
              "Studious", "Attentive", "Thorough", "Motivated", "Tireless", "Driven", "Persistent", "Committed",
              "Earnest", "Passionate", "Dedicated", "Energetic", "Sincere", "Determined", "Genuine", "Spirited",
              "Devoted", "Wholehearted", "Accomplished", "Adept", "Ideal", "Industrious", "Competent", "Influential",
              "Constructive", "Instrumental", "Productive", "Proficient", "Qualified", "Profitable", "Cutting-edge",
              "Ingenious", "Innovative", "First-class", "Groundbreaking", "Progressive", "Imaginative", "Revolutionary",
              "World-class", "Astute", "Intelligent", "Perceptive", "Logical", "Practical", "Methodical", "Strategic",
              "Insightful", "Thoughtful"]
worker_names = ["worker", "candidate", "job seeker", "team player"]
with open("resources/generators/job_dataset.json") as f:
    job_list = list(json.load(f).keys())
skill_levels = ["novice", "familiar", "competent", "proficient", "expert"]
edu_types = ["certification", "Associate's degree", "Bachelor's degree", "Master's degree", "Doctorate"]

# In order: full, part, full/part, contract, full/contract, part/contract, any
# Based on https://www.bls.gov/cps/cpsaat19.htm
# and https://www.bls.gov/opub/ted/2018/independent-contractors-made-up-6-point-9-percent-of-employment-in-may-2017.htm
worktype_weights = [75, 25, 19, 7, 5, 2, 1]


def generate_history_education() -> dict:
    choice = random.choice(school_templates)
    _state = fake.state()
    _first = fake.first_name()
    _last = fake.last_name()
    _company = re.sub(" .+", "", fake.company())
    _type = "University" if random.random() <= 0.5 else "College"

    school = choice.format(state=_state, first=_first, last=_last, company=_company, schooltype=_type)
    level = random.randint(0, 4)
    degree = random.choice(degrees)
    return {"school": school, "education_lvl": level, "study_field": degree}


def generate_history_job() -> dict:
    return {
        "job_title": random.choice(job_list),
        "years_employed": random.randint(1, 10)}


def generate_profile(is_male=None) -> dict:
    if is_male is None:
        is_male = random.random() <= 0.5

    profile = dict()
    if is_male:
        profile['first_name'] = fake.first_name_male()
        # profile['sex'] = 'male'
    else:
        profile['first_name'] = fake.first_name_female()
        # profile['sex'] = 'female'
    profile['last_name'] = fake.last_name()

    zip_code, city, state = barnum.create_city_state_zip()
    profile['city'] = city
    profile['state'] = state
    # profile['zip_code'] = zip_code
    # remove non-digits from phone
    profile['phone_number'] = re.sub(r"[^\d]", "", barnum.create_phone(zip_code))

    email = barnum.create_email(name=[profile['first_name'], profile['last_name']])
    # custom overrides for email
    email = (email[:email.index("@") + 1] + random.choice(domains)).lower()
    profile['email'] = email

    profile['join_date'] = fake.date_time_this_year()

    # worktype ranges from 1-7
    profile['work_wanted'] = random.choices(range(1, 8), worktype_weights)[0]
    profile['remote_wanted'] = random.random() <= 0.5  # just a guess

    return profile


def generate_attributes(att_rng, biz_rng, tech_rng) -> dict:
    """
    Outputs a dictionary of 'values' and 'skills' (both 'biz', and 'tech'),
    with the skills having a 'level' attribute.
    """
    attrs = dict()
    attrs["values"] = gen_values(att_rng)
    attrs["skills"] = {"biz": gen_biz(biz_rng), "tech": gen_tech(tech_rng)}
    return attrs


def ordered_skills(skills: dict) -> Tuple[List[List[str]], List[int]]:
    # get reverse ordered pair of 'name', 'int_level'
    spairs = skills.items()
    spairs = [(i[0], i[1]['level']) for i in spairs]
    spairs.sort(key=itemgetter(1), reverse=True)
    slists, slvls = [], []
    if len(spairs) == 0:
        return slists, slvls
    slist, last_lvl = [], spairs[0][1]
    for skl, lvl in spairs:
        if lvl == last_lvl:
            slist.append(skl)
        else:
            slists.append(slist)
            slvls.append(last_lvl)

            slist = [skl]
            last_lvl = lvl
    if slist:
        slists.append(slist)
        slvls.append(last_lvl)
    return slists, slvls


def gen_summary():
    p = random.randint(3, 5)
    summary = "\n".join(fake.paragraphs(nb=p, ext_word_list=None))
    return summary


def gen_tagline(profile: SeekerProfile) -> str:

    # intro
    _adj = random.choice(adjectives)
    if profile.min_edu_level > 0 and random.random() < 0.7:
        phrase0 = f"{_adj} graduate"
    elif profile.years_job_experience > 0 and random.random() < 0.7:
        _jtitle = random.choice(profile._history_jobs).job_title
        phrase0 = f"Ex-{_jtitle}"
        if random.random() < 0.3:
            phrase0 += " transitioning into a new role"
    else:
        phrase0 = f"{_adj} {random.choice(worker_names)}"

    # main phrase
    phrase1 = "who"
    _nskills = len(profile._skills)
    if _nskills < 6 and random.random() < 0.8:
        # set a default list in case nothing is set in the seeker
        _skl_lvls = profile.get_biz_skills_levels()+profile.get_tech_skills_levels() or [('Thing', 5)]
        max_lvl = max(_skl_lvls, key=itemgetter(1))[1]
        if max_lvl <= 3:  # competent
            phrase1 += random.choice([" is just getting started", " is ready to learn"])
        else:
            phrase1 += random.choice([" is dedicated to the craft", " is a specialist"])
    elif _nskills > 10 and random.random() < 0.8:
        phrase1 += random.choice([" has many skills", " has a diverse set of skills"])
    else:
        phrase1 += random.choice([" is passionate about work", " is eager to work", " has proven experience",
                                  " brings unique assets", " aspires for greatness"])

    # possibly end it here
    if 100 >= len(phrase0+phrase1) > 80 or random.random() < 0.2:
        return f"{phrase0} {phrase1}."

    # secondary phrase (join by 'and' if adding the main phrase)
    # set a default list of attitudes in case nothing is set in the seeker.
    _atts = profile.get_attitudes() or ['things']
    phrase2 = random.choice(["values ", "deeply values ", "seeking a role that values ", "embraces the notion of "]) \
              + random.choice(_atts).lower()

    # concluding phrase (a new sentence)
    phrase3 = random.choice(["", "", "", "Eager to talk!", "Eager to hear from you.", "Feel free to reach out!",
                             "Feel free to email/call.", "See my profile for more!", "Hire me!", "Contact me!"])

    # find shortest combo that fits
    join01, join02, join12, joinx3 = " ", ", ", " and ", ". "

    len0, len1, len2, len3 = len(phrase0), len(phrase1), len(phrase2), len(phrase3)
    len_join01 = len(join01)  # " "
    len_join02 = len(join02)  # ", "
    len_join12 = len(join12)  # " and "
    len_joinx3 = len(joinx3)  # ". "
    if len0 + len_join01 + len1 + len_join12 + len2 + len_joinx3 + len3 < 100:
        # 0123
        return f"{phrase0}{join01}{phrase1}{join12}{phrase2}{joinx3}{phrase3}"
    elif len0 + len_join01 + len1 + len_join12 + len2 < 100 and random.random() < 0.75:
        # 012
        return f"{phrase0}{join01}{phrase1}{join12}{phrase2}."
    elif len0 + len_join01 + len1 + len_joinx3 + len3 < 100 and random.random() < 0.5:
        # 013
        return f"{phrase0}{join01}{phrase1}{joinx3}{phrase3}"
    elif len0 + len_join02 + len2 + len_joinx3 + len3 < 100 and random.random() < 0.5:
        # 023
        return f"{phrase0}{join02}{phrase2}{joinx3}{phrase3}"
    elif len0 + len_join01 + len1 < 100 and random.random() < 0.3:
        # 01
        return f"{phrase0}{join01}{phrase1}."
    elif len0 + len_join02 + len2 < 100 and random.random() < 0.3:
        # 02
        return f"{phrase0}{join02}{phrase2}."
    elif len0 + len_joinx3 + len3 < 100 and random.random() < 0.3:
        # 03
        return f"{phrase0}{joinx3}{phrase3}"
    return f"{phrase0}."

# def make_resume(person: dict, attrs: dict = None, output_dir: str = None):
#     values = attrs['values']
#     skills1 = attrs['skills']['tech']
#     skills2 = attrs['skills']['biz']
#     if values is None: values = []
#     if skills1 is None: skills1 = []
#     if skills2 is None: skills2 = []
#     # generate description for person
#     description = random.choice(phrases).format(phrase=fake.catch_phrase().lower())
#     if values:
#         description += " Things I value include: " + ", ".join(values)
#
#     document = MailMerge("resume_template.docx")
#     document.merge(
#         first = person['first_name'],
#         last = person['last_name'],
#         location = person['city'] + ", " + person['state'],
#         phone = f"({person['phone'][:3]}){person['phone'][3:6]}-{person['phone'][6:]}",
#         email = person['email'],
#         headline=description,
#         skills1 = "\n".join(skills1),
#         skills2 = "\n".join(skills2)
#     )
#     fn = f"resume_{person['first_name']}_{person['last_name']}.docx"
#     if output_dir is not None:
#         fn = os.path.join(output_dir, fn)
#     document.write(fn)
#     return fn
