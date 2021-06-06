# TODO implement funcs for performing matching
# (Maybe split into separate sub-library if needed and have this as a public end-point)
from app.models import SeekerProfile, JobPost, CompanyProfile


def get_score(jobpost_id, seeker_id):
    # Point values
    WITHIN_50_MILES = 25
    WITHIN_100_MILES = 15
    SKILL_HIGH_IMPORTANCE = 6
    SKILL_LOW_IMPORTANCE = 4
    SAME_ATTITUDE = 6

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
        if job_skill._skill.title not in seeker_skill_lookup:
            continue

        # get attribute from jobpost tuple
        title = job_skill[0]
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
        job_attitudes_list.append(job_attitude_tuple[0])

    seeker_attitudes = seeker.get_attitudes()
    matching_attitudes = set(job_attitudes_list).intersection(set(seeker_attitudes))

    for matching_attitude in matching_attitudes:
        matching_index = [i[0] for i in job_attitudes].index(
            matching_attitude)  # get index of current attitudes in job attitudes
        importance_level = job_attitudes[matching_attitude][1]  # get importance level from 2nd index of tuple
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
        jobs_by_score.append((job_id, score))

    jobs_by_score_sorted = sorted(jobs_by_score, key=lambda tup: tup[1])

    # I'm bad at programming and I don't know how to do this below I'm sorry :')
    # jobs_by_score = sorted(jobs_list, key=lambda jid: get_score(seeker_id, jid))

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
        seekers_by_score.append((seeker_id, score))

    seekers_by_score_sorted = sorted(seekers_by_score, key=lambda tup: tup[1])
    return seekers_by_score_sorted