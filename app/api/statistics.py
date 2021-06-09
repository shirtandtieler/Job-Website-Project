# A file for querying various statistics
from functools import cmp_to_key

from sqlalchemy import func

from app import db
from app.models import SeekerProfile, LocationCoordinates, CompanyProfile, JobPost, Skill, SeekerSkill, SkillTypes, \
    Attitude, SeekerAttitude, JobPostSkill, JobPostAttitude


def get_coordinate_info(table, describe=False, merge=False):
    """
    Gets the coordinates from the locations of each entry in the given table.
    If `describe` is true, will also append the location name.
    If `merge` is true, will combine entries of the location and append the count.
    """
    entries = table.query.all()
    counts = dict()
    # first get all info - coordinates, names, and counts
    for entry in entries:
        try:
            lat, lng = LocationCoordinates.get(entry.city, entry.state, False)
            name = f"{entry.city}, {entry.state}"
            # could not find one or the other; just replace with unknown for city and 'USA' for state
            if name.startswith("None"):
                name = name.replace("None", "Unknown", 1)
            if "None" in name:  # state is unknown
                name = name.replace("None", "USA")

        except ValueError:
            try:
                lat, lng = LocationCoordinates.get(state=entry.state, fallback=False)
                name = entry.state
            except ValueError:
                lat, lng = LocationCoordinates.get(None, None, True)
                name = "Unknown"
        key = (lat, lng, name)
        counts[key] = counts.setdefault(key, 0) + 1

    # then extract content based on arguments
    if merge:
        # append count to the tuple, slicing to remove the name if it's not wanted
        return [(*k, v) if True else (*k[:-1], v) for k, v in counts.items()]
    # get and unpack the duplicated entries (repeated v times)
    # slice tuple if not wanting the location description
    i = 3 if describe else 2
    return [x for y in [[k[:i] for _ in range(v)] for k, v in counts.items()] for x in y]


def _cmp(name_count_1, name_count_2):
    # custom comparator so that things are sorted first by the value @ index 1 in reverse order,
    #   then by the value @ index 0 in non-reverse order
    return (name_count_2[1]-name_count_1[1])*2 + (1 if name_count_1[0]>name_count_2[0] else -1)


def get_seeker_counts_by_skill(skill_type: str):
    results = db.session.query(Skill.title, func.count(SeekerSkill.id))
    if skill_type == 't':
        results = results.filter_by(type=SkillTypes.t)
    elif skill_type == 'b':
        results = results.filter_by(type=SkillTypes.b)
    results = results.join(Skill._seekers)\
        .group_by(Skill.id)\
        .all()
    results.sort(key=cmp_to_key(_cmp))
    return results


def get_seeker_counts_by_attitude():
    results = db.session.query(Attitude.title, func.count(SeekerAttitude.id))\
        .join(Attitude._seekers) \
        .group_by(Attitude.id) \
        .all()
    results.sort(key=cmp_to_key(_cmp))
    return results


def get_post_counts_by_skill(skill_type: str):
    results = db.session.query(Skill.title, func.count(JobPostSkill.id))
    if skill_type == 't':
        results = results.filter_by(type=SkillTypes.t)
    elif skill_type == 'b':
        results = results.filter_by(type=SkillTypes.b)
    results = results.join(Skill._job_posts) \
        .group_by(Skill.id) \
        .all()
    results.sort(key=cmp_to_key(_cmp))
    return results


def get_post_counts_by_attitude():
    results = db.session.query(Attitude.title, func.count(JobPostAttitude.id)) \
        .join(Attitude._job_posts) \
        .group_by(Attitude.id) \
        .all()
    results.sort(key=cmp_to_key(_cmp))
    return results
