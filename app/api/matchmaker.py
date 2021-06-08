from app import db
from app.models import SeekerProfile, JobPost, CompanyProfile, Skill, Attitude, MatchScores


def update_cache(jobpost_id: int = None, seeker_id: int = None):
    """
    Update the database cache for the given job post and/or the seeker
        (when nothing is passed, everything will be updated)
    """
    posts = JobPost.query
    if jobpost_id is not None:
        posts = posts.filter_by(id = jobpost_id)
    posts = posts.all()

    seekers = SeekerProfile.query
    if seeker_id is not None:
        seekers = seekers.filter_by(id=seeker_id)
    seekers = seekers.all()

    for post in posts:
        for seeker in seekers:
            entry = MatchScores(jobpost_id=post.id, seeker_id=seeker.id,
                                score=get_score(post.id, seeker.id, False))
            db.session.add(entry)
    db.session.commit()


def get_score(jobpost_id, seeker_id, from_cache=True):
    if from_cache:
        entry = MatchScores.query.filter_by(jobpost_id=jobpost_id, seeker_id=seeker_id).first()
        if entry is None:  # not in cache!
            score = get_score(jobpost_id, seeker_id, False)
            entry = MatchScores(jobpost_id=jobpost_id, seeker_id=seeker_id, score=score)
            db.session.add(entry)
            db.session.commit()
        return entry.score

    # Point values
    WITHIN_50_MILES = 25
    WITHIN_100_MILES = 15
    SKILL_HIGH_IMPORTANCE = 7
    SKILL_LOW_IMPORTANCE = 5
    SAME_ATTITUDE = 4

    post = JobPost.query.filter_by(id=jobpost_id).first()
    if post is None:
        raise ValueError(f"No job post with the ID of {jobpost_id}")

    company_id = post.company_id
    company = CompanyProfile.query.filter_by(id=company_id).first()
    if company is None:
        raise ValueError(f"Company with id {company_id} could not be found")

    seeker = SeekerProfile.query.filter_by(id=seeker_id).first()
    if seeker is None:
        raise ValueError(f"Seeker with id {seeker_id} could not be found.")

    seeker_points = 0  # initiate seeker points to 0

    if post.is_remote is False:
        if seeker.is_within(50, post.city, post.state):
            seeker_points += WITHIN_50_MILES
        elif seeker.is_within(100, post.city, post.state):
            seeker_points += WITHIN_100_MILES

    job_skills = post.get_skills_data()
    seeker_skills = seeker.get_tech_skills_levels() + seeker.get_biz_skills_levels()
    seeker_skill_lookup = dict(seeker_skills)

    # match and give points for skills
    for job_skill in job_skills:

        # get job title from id
        skill_id = job_skill[0]
        skill = Skill.query.filter_by(id=skill_id).first()
        title = skill.title

        if title not in seeker_skill_lookup:
            continue

        # get attribute from jobpost tuple
        job_skill_level = job_skill[1]
        importance_level = job_skill[2]

        # get skill level from seeker
        seeker_skill_level = seeker_skill_lookup.get(title, 0)  # default of 0 in case the skill doesn't exist somehow

        if importance_level > 3:  # importance level is 4 or 5
            if seeker_skill_level >= job_skill_level:
                seeker_points += SKILL_HIGH_IMPORTANCE
                bonus_points = seeker_skill_level - job_skill_level
                bonus_points = bonus_points * 1.5  # bonus multiplier for high importance
                seeker_points += bonus_points

        if importance_level < 4:
            if seeker_skill_level >= job_skill_level:
                seeker_points += SKILL_LOW_IMPORTANCE
                bonus_points = seeker_skill_level - job_skill_level
                seeker_points += bonus_points
            if seeker_skill_level == job_skill_level - 1:
                seeker_points += SKILL_LOW_IMPORTANCE / 2
            if seeker_skill_level == job_skill_level - 2:
                seeker_points += SKILL_LOW_IMPORTANCE / 3

    # match and give points for attitudes
    job_attitudes = post.get_attitude_data()  # list of tuples

    job_attitudes_list = []  # list of attitudes only from job post # to intersect with seeker_attitudes
    for job_attitude_tuple in job_attitudes:

        attitude_id = job_attitude_tuple[0]
        attitude = Attitude.query.filter_by(id=attitude_id).first()
        title = attitude.title

        job_attitudes_list.append(title)

    seeker_attitudes = seeker.get_attitudes()
    matching_attitudes = set(job_attitudes_list).intersection(set(seeker_attitudes))

    for matching_attitude in matching_attitudes:

        matching_attitude_id = Attitude.query.filter_by(title=matching_attitude).first().id # get id of the attitude
        matching_index = [i[0] for i in job_attitudes].index(matching_attitude_id)  # get index of tuble of the current matching_attitude in job_attitudes
        importance_level = job_attitudes[matching_index][1]  # get importance level from 2nd index of tuple

        multiplier = importance_level / 2
        seeker_points += SAME_ATTITUDE * multiplier

    return seeker_points

#returns a list of tuples where the t
def get_jobs_sorted(seeker_id, jobs_list=None, limit=50):
    """
    Get a list of the best matching jobs for a seeker, where each entry contains:
        1. The job id
        2. The score the seeker got for that particular job (used for sorting jobs)
    """
    if jobs_list is None:
        jobs_list = [job.id for job in JobPost.query.all()]
    # maybe pass some options to `get_score` in the following call
    jobs_by_score = []
    for job_id in jobs_list:
        score = get_score(job_id, seeker_id)
        if score > 0:
            jobs_by_score.append((job_id, score))

    jobs_by_score_sorted = sorted(jobs_by_score, key=lambda tup: tup[1])
    jobs_by_score_sorted.reverse()
    return jobs_by_score_sorted[:limit]


def get_seekers_sorted(job_id, seeker_list=None, limit=50):
    """
    Get a list of the best matching seekers for a job, where each entry contains:
        1. The seeker id
        2. The score that particular seeker got for the given job (used for sorting seekers)
    """
    if seeker_list is None:
        seeker_list = [seeker.id for seeker in SeekerProfile.query.all()]

    seekers_by_score = []
    for seeker_id in seeker_list:
        score = get_score(job_id, seeker_id)
        if score > 0:
            seekers_by_score.append((seeker_id, score))

    seekers_by_score_sorted = sorted(seekers_by_score, key=lambda tup: tup[1])
    seekers_by_score_sorted.reverse()
    return seekers_by_score_sorted[:limit]
