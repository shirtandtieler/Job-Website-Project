import traceback
from typing import Tuple, Union, List

from app import db
from app.models import JobPost, JobPostSkill, SkillLevels, ImportanceLevel, Skill, JobPostAttitude, Attitude


def new_jobpost(company_id: int, title: str,
                city: str = None, state: str = None, description: str = None, remote: bool = None,
                salary_range: Tuple[int, int] = None,
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
    post = JobPost(company_id=company_id, job_title=title,
                   city=city, state=state, description=description,
                   is_remote=remote)
    if salary_range is not None:
        post.salary_min = salary_range[0]
        post.salary_max = salary_range[1]

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
            print(f"DEBUG: Creating job post skill for pid {post.id}, attitude id {sid}, skl lvl {slvl}, imp lvl {simp}")
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
            print(f"DEBUG: Creating job post attitude for pid {post.id}, attitude id {aid}, imp lvl {aimp}")
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
                 remote: bool = None, salary_range: Tuple[Union[None, int], Union[None, int]] = None,
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
    if remote:
        post.is_remote = remote
    if salary_range:
        if salary_range[0]:
            post.salary_min = salary_range[0]
        if salary_range[1]:
            post.salary_max = salary_range[1]
    if skills:
        # make a dictionary mapping new ids to their level/importance
        # to make it easy to query differences.
        new_skill_lookup = dict()
        for skl, slvl, simp in skills:
            sid = skl if isinstance(skl, int) else Skill.query.filter_by(title=skl).first()
            new_skill_lookup[sid] = (slvl, simp)
        # compare existing skills with new proposed list, editing or deleting as necessary
        for jp_skill in post._skills:
            if jp_skill.skill_id in new_skill_lookup:  # skill is in the new list, update its values
                jp_skill.skill_level_min = SkillLevels(new_skill_lookup[jp_skill.skill_id][0])
                jp_skill.importance_level = ImportanceLevel(new_skill_lookup[jp_skill.skill_id][1])
                # now pop out of dictionary so that it wont be added in the following step
                _ = new_skill_lookup.pop(jp_skill.skill_id)
            else:  # skill wasn't included in new list; assume deletion
                db.session.delete(jp_skill)
        # for the remaining skills in the dict, add them in
        for sid, (slvl, simp) in new_skill_lookup.items():
            jp_skill = JobPostSkill(jobpost_id=post.id, skill_id = sid, skill_level_min = slvl, importance_level = simp)
            db.session.add(jp_skill)
    if attitudes:
        # make a dictionary mapping new ids to their importance
        # to make it easy to query differences
        new_att_lookup = dict()
        for att, aimp in attitudes:
            aid = att if isinstance(att, int) else Attitude.query.filter_by(title=att).first()
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
            jp_att = JobPostAttitude(jobpost_id=post.id, attitude_id = aid, importance_level = aimp)
            db.session.add(jp_att)

    # submit all changes
    db.session.commit()

