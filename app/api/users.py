# TODO add functions to create/update/get entries in database related to users or their account/profile
from typing import Union

from app import db
from app.models import AccountTypes, WorkTypes, SkillLevels, SeekerSkill, SeekerAttitude, EducationLevel, \
    SeekerHistoryEducation, SeekerHistoryJob, CompanySeekerSearch, SeekerJobSearch, Skill, Attitude
from app.models import User, CompanyProfile, SeekerProfile


# TODO should add arg for commiting? May increase performance when updating in bulk

def save_seeker_search(user_id, label, query):
    entry = CompanySeekerSearch(user_id=user_id, label=label, query=query)
    db.session.add(entry)
    db.session.commit()


def delete_seeker_search(user_id, label, query):
    entry = db.session.query(CompanySeekerSearch).filter_by(user_id=user_id, label=label, query=query).first()
    if entry is None:
        raise ValueError(f"No such search from user {user_id} w/ label {label} and query {query}")
    db.session.delete(entry)
    db.session.commit()


def save_job_search(user_id, label, query):
    entry = SeekerJobSearch(user_id=user_id, label=label, query=query)
    db.session.add(entry)
    db.session.commit()


def delete_job_search(user_id, label, query):
    entry = db.session.query(SeekerJobSearch).filter_by(user_id=user_id, label=label, query=query).first()
    if entry is None:
        raise ValueError(f"No such search from user {user_id} w/ label {label} and query {query}")
    db.session.delete(entry)
    db.session.commit()


def new_company(email, password, join_date=None,
                name=None, city=None, state=None, website=None,
                tagline=None, summary=None):
    """
    Adds a new Company to the database.
    """
    user = User()
    user.account_type = AccountTypes.c
    user.email = email
    user.set_password(password)
    if join_date is not None:
        user.join_date = join_date

    # before the profile can be created, it needs to committed
    # (as that's when the id field is generated)
    db.session.add(user)
    db.session.commit()

    profile = CompanyProfile()
    profile.user_id = user.id
    # for name, need to set some non-none defaults to satisfy db
    profile.name = name or email[email.index('@') + 1:email.rindex('.')]  # domain part of email
    profile.city = city
    profile.state = state
    profile.website = website
    profile.tagline = tagline
    profile.summary = summary
    db.session.add(profile)
    db.session.commit()


def edit_company(company_id,
                 name=None, city=None, state=None, website=None,
                 tagline=None, summary=None):
    profile = CompanyProfile.query.filter_by(id=company_id).first()
    if profile is None:
        raise ValueError(f"Company with id {company_id} could not be found.")
    if name is not None:
        profile.name = name
    if city is not None:
        profile.city = city
    if state is not None:
        profile.state = state
    if website is not None:
        # > 0 check to make sure user isn't just wanting to delete the website url
        if len(website) > 0 and not website.startswith("http"):
            website = "http://" + website
        profile.website = website
    if tagline is not None:
        profile.tagline = tagline
    if summary is not None:
        profile.summary = summary
    db.session.commit()


def new_seeker(email, password, join_date=None,
               first_name=None, last_name=None,
               phone_number=None,
               city=None, state=None,
               work_wanted=WorkTypes.any, remote_wanted=False,
               tagline=None, summary=None,
               resume=None
               ):
    """
    Adds a new Seeker to the database.
    """
    user = User()
    user.account_type = AccountTypes.s
    user.email = email
    user.set_password(password)
    if join_date is not None:
        user.join_date = join_date

    # before the profile can be created, it needs to committed
    # (as that's when the id field is generated)
    db.session.add(user)
    db.session.commit()

    profile = SeekerProfile()
    profile.user_id = user.id
    # for first and last name, need to set some non-none defaults to satisfy db
    profile.first_name = first_name or email[:email.index('@')]  # username part of email
    profile.last_name = last_name or "Seeker"
    profile.phone_number = phone_number
    profile.city = city
    profile.state = state
    profile.work_wanted = WorkTypes(work_wanted or WorkTypes.any)
    profile.remote_wanted = remote_wanted or False
    profile.tagline = tagline
    profile.summary = summary
    profile.resume = resume

    db.session.add(profile)
    db.session.commit()
    return profile.id


def edit_seeker(seeker_id,
                first_name: str = None, last_name: str = None,
                phone_number: str = None,
                city: str = None, state: str = None,
                work_wanted: WorkTypes = None, remote_wanted: bool = False,
                tagline: str = None, summary: str = None,
                resume: bin = None
                ):
    """
    Edits a seeker in the database
    """
    profile = SeekerProfile.query.filter_by(id=seeker_id).first()
    if profile is None:
        raise ValueError(f"Seeker with id {seeker_id} could not be found.")
    if first_name is not None:
        profile.first_name = first_name
    if last_name is not None:
        profile.last_name = last_name
    if phone_number is not None:
        profile.phone_number = phone_number
    if city is not None:
        profile.city = city
    if state is not None:
        profile.state = state
    if work_wanted is not None:
        profile.work_wanted = work_wanted
    if remote_wanted is not None:
        profile.remote_wanted = remote_wanted
    if tagline is not None:
        profile.tagline = tagline
    if summary is not None:
        profile.summary = summary
    if resume is not None:
        profile.resume = resume
    db.session.commit()


def reset_seeker(seeker_id: int, skills=False, attitudes=False, educations=False, jobs=False):
    seeker = SeekerProfile.query.filter_by(id=seeker_id).first()
    counts = []
    if skills:
        counts.append(len(seeker._skills))
        for entry in seeker._skills:
            db.session.delete(entry)
    if attitudes:
        counts.append(len(seeker._attitudes))
        for entry in seeker._attitudes:
            db.session.delete(entry)
    if educations:
        counts.append(len(seeker._history_edus))
        for entry in seeker._history_edus:
            db.session.delete(entry)
    if jobs:
        counts.append(len(seeker._history_jobs))
        for entry in seeker._history_jobs:
            db.session.delete(entry)
    db.session.commit()
    return counts


def update_seeker_skill(seeker_id: int, skill: Union[int, str], skill_level: Union[int, SkillLevels]):
    """ Adds or updates a seeker's skill """
    if isinstance(skill_level, int):
        skill_level = SkillLevels(skill_level)
    if isinstance(skill, str):
        skill_id = Skill.query.filter_by(id=skill).first()
    else:
        skill_id = skill
    # check if adding or updating
    entry = SeekerSkill.query.filter_by(seeker_id=seeker_id, skill_id=skill_id).first()
    if entry is None:
        entry = SeekerSkill(seeker_id=seeker_id, skill_id=skill_id, skill_level=skill_level)
        db.session.add(entry)
    else:
        entry.skill_level = skill_level
    db.session.commit()


def remove_seeker_skill(seeker_id, skill_id):
    """
    Removes skill for a seeker.
    """
    entry = SeekerSkill.query.filter_by(seeker_id=seeker_id, skill_id=skill_id)
    if entry is None:
        raise ValueError(f"Seeker with ID {seeker_id} does not possess skill with ID {skill_id}")
    db.session.delete(entry)
    db.session.commit()


def add_seeker_attitude(seeker_id: int, attitude: Union[int, str], error_if_fail=False):
    """ Adds a seeker's attitude. """
    attitude_id = attitude if isinstance(attitude, int) else Attitude.query.filter_by(title=attitude).first()
    entry = SeekerAttitude.query.filter_by(seeker_id=seeker_id, attitude_id=attitude_id).first()
    if entry is not None:  # already added
        if error_if_fail:
            raise ValueError(f"Seeker with ID {seeker_id} already possesses attitude with ID {attitude_id}: entry {entry.id}")
        return
    entry = SeekerAttitude(seeker_id=seeker_id, attitude_id=attitude_id)
    db.session.add(entry)
    db.session.commit()


def remove_seeker_attitude(seeker_id: int, attitude_id: int):
    """ Removes a seeker's attitude """
    entry = SeekerAttitude.query.filter_by(seeker_id=seeker_id, attitude_id=attitude_id)
    if entry is None:
        raise ValueError(f"Seeker with ID {seeker_id} does not have attitude with ID {attitude_id}")
    db.session.delete(entry)
    db.session.commit()


def add_seeker_education(seeker_id: int, school: str, education_lvl: int, study_field: str):
    entry = SeekerHistoryEducation(seeker_id=seeker_id, school=school,
                                   education_lvl=EducationLevel(education_lvl), study_field=study_field)
    db.session.add(entry)
    db.session.commit()


def remove_seeker_education(seeker_id: int, edu_id: int):
    raise NotImplementedError()


def add_seeker_job(seeker_id: int, job_title: str, years_employed: int):
    entry = SeekerHistoryJob(seeker_id=seeker_id, job_title=job_title, years_employed=years_employed)
    db.session.add(entry)
    db.session.commit()


def remove_seeker_job(seeker_id: int, job_id: int):
    raise NotImplementedError()


def new_admin(email, password):
    """
    Adds a new admin user to the database
    """
    user = User()
    user.account_type = AccountTypes.a
    user.email = email
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    # TODO add profile after creating adminprofile table
