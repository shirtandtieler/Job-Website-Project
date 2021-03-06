import traceback
from typing import Tuple, Union, List

from app import db
from app.models import JobPost, JobPostSkill, SkillLevels, ImportanceLevel, Skill, JobPostAttitude, Attitude, WorkTypes


def extract_details(form):
    # convert the fields to None that would otherwise just be empty string.
    # (to preserve the default values of the new job function)
    details = dict()
    details['title'] = form.title.data
    details['city'] = form.city.data if form.city.data else None
    details['state'] = form.state.data if form.state.data else None
    details['description'] = form.description.data if form.description.data else None
    # convert work type boolean fields to integer
    wt_int = int(form.work_types.data.get('full_time', False)) * int(WorkTypes.full) \
             + int(form.work_types.data.get('part_time', False)) * int(WorkTypes.part) \
             + int(form.work_types.data.get('contract', False)) * int(WorkTypes.contract)
    details['work_type'] = wt_int
    details['remote'] = form.remote.data
    details['salary'] = (form.salary_min.data, form.salary_max.data)
    details['active'] = form.active.data
    # convert the passed skills and attitudes to the expected format
    details['skills'] = [(s['skill'], int(s['min_lvl']), int(s['importance'])) for s in form.req_skills.data]
    details['attitudes'] = [(a['att'], int(a['importance'])) for a in form.req_attitudes.data]
    return details


def new_jobpost(company_id: int, title: str,
                city: str = None, state: str = None, description: str = None,
                work_type: int = None, remote: bool = None,
                salary: Tuple[int, int] = None, active: bool = True,
                skills: List[Tuple[Union[str, int], int, int]] = None,
                attitudes: List[Tuple[Union[str, int], int]] = None) -> int:
    """
    Create a new job post, passing - at minimum - the company ID and job post title.
    Can also pass other fields of the job post, including a list of skill and attitude requirements.
    If skills are passed, each element in the list should contain 3 values: 
        1. the name or id of the skill,
        2. the minimum skill level (1-5)
        3. the importance level (0-5)
    If attitudes are passed, each element in the list should contain 2 values:
        1. the name or id of the attitude,
        2. the importance level (0-5)
    Returns the id of the added job post.
    """
    if work_type is None:
        work_type = int(WorkTypes.any)
    post = JobPost(company_id=company_id, job_title=title,
                   city=city, state=state, description=description,
                   work_type=WorkTypes(work_type), is_remote=remote,
                   active=active)
    if salary is not None:
        post.salary_min = salary[0]
        post.salary_max = salary[1]

    # before skills/attitudes can be added, commit changes
    # so that the id is loaded
    db.session.add(post)
    db.session.commit()

    if skills is not None:
        for (skl, slvl, simp) in skills:
            if isinstance(skl, str):  # convert to int id
                sid = Skill.query.filter_by(title=skl).first().id
            else:
                sid = skl
            post_skill = JobPostSkill(jobpost_id=post.id,
                                      skill_id=sid,
                                      skill_level_min=SkillLevels(slvl),
                                      importance_level=ImportanceLevel(simp))
            db.session.add(post_skill)
    if attitudes is not None:
        for (att, aimp) in attitudes:
            if isinstance(att, str):  # convert to int id
                aid = Attitude.query.filter_by(title=att).first().id
            else:
                aid = att
            post_attitude = JobPostAttitude(jobpost_id=post.id,
                                            attitude_id=aid,
                                            importance_level=ImportanceLevel(aimp))
            db.session.add(post_attitude)
    if skills or attitudes:
        try:
            db.session.commit()
        except:
            traceback.print_exc()
            print("<<<< ROLLING BACK! >>>>")
            db.session.rollback()

    return post.id


def edit_jobpost(post_id: int,
                 title: str = None, city: str = None, state: str = None, description: str = None,
                 work_type: int = None, remote: bool = None, salary: Tuple[Union[None, int], Union[None, int]] = None,
                 active: bool = None,
                 skills: List[Tuple[Union[str, int], int, int]] = None,
                 attitudes: List[Tuple[Union[str, int], int]] = None):
    """
    Update the provided job post with the specified values.
    If updating salary range, can pass None for any value in the 2-tuple that you don't want to update.
    If updating skills or attitudes, it will override the existing entries entirely - so any that you
        don't include in this list will be deleted.
    If skills are passed, each element in the list should contain 3 values: 
        1. the name or id of the skill
        2. the minimum skill level (1-5)
        3. the importance level (0-5)
    If attitudes are passed, each element in the list should contain 2 values:
        1. the name or id of the attitude
        2. the importance level (0-5)
    Returns nothing.
    """
    post = JobPost.query.filter_by(id=post_id).first()
    if post is None:
        raise ValueError(f"No job post with the ID of {post_id}")
    if title:
        post.job_title = title
    if city:
        post.city = city
    if state:
        post.state = state
    if description:
        post.description = description
    if work_type:
        post.work_type = WorkTypes(work_type)
    if remote is not None:
        post.is_remote = remote
    if salary:
        if salary[0]:
            post.salary_min = salary[0]
        if salary[1]:
            post.salary_max = salary[1]
    if active is not None:
        post.active = active
    if skills:
        # make a dictionary mapping new ids to their level/importance
        # to make it easy to query differences.
        new_skill_lookup = dict()
        for skl, slvl, simp in skills:
            sid = skl if isinstance(skl, int) else Skill.query.filter_by(title=skl).first().id
            new_skill_lookup[sid] = (slvl, simp)
        # compare existing skills with new proposed list, editing or deleting as necessary
        for jp_skill in post._skills:
            if jp_skill.skill_id in new_skill_lookup:  # skill is in the new list, update its values
                jp_skill.skill_level_min = SkillLevels(new_skill_lookup[jp_skill.skill_id][0])
                jp_skill.importance_level = ImportanceLevel(new_skill_lookup[jp_skill.skill_id][1])
                # now pop out of dictionary so that it wont be added in the following step
                _ = new_skill_lookup.pop(jp_skill.skill_id)
                print(f"Update skill {jp_skill}")
            else:  # skill wasn't included in new list; assume deletion
                db.session.delete(jp_skill)
                print(f"Delete skill {jp_skill}")
        # for the remaining skills in the dict, add them in
        for sid, (slvl, simp) in new_skill_lookup.items():
            jp_skill = JobPostSkill(jobpost_id=post.id, skill_id=sid, skill_level_min=slvl, importance_level=simp)
            db.session.add(jp_skill)
            print(f"Add skill {jp_skill}")
    if attitudes:
        # make a dictionary mapping new ids to their importance
        # to make it easy to query differences
        new_att_lookup = dict()
        for att, aimp in attitudes:
            aid = att if isinstance(att, int) else Attitude.query.filter_by(title=att).first().id
            new_att_lookup[aid] = aimp
        # compare existing attitudes with new proposed list, editing or deleting as necessary
        for jp_att in post._attitudes:
            if jp_att.attitude_id in new_att_lookup:  # attitude is in the new list, update its value
                jp_att.importance_level = ImportanceLevel(new_att_lookup[jp_att.attitude_id])
                # now pop out of dictionary so that it wont be added in the following step
                _ = new_att_lookup.pop(jp_att.attitude_id)
            else:  # attitude wasn't included in the new list; assume deletion
                db.session.delete(jp_att)
        # for the remaining attitudes in the dict, add them in
        for aid, aimp in new_att_lookup.items():
            jp_att = JobPostAttitude(jobpost_id=post.id, attitude_id=aid, importance_level=aimp)
            db.session.add(jp_att)

    # submit all changes
    db.session.commit()
