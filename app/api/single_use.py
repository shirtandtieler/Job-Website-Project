# A script for single-use functions
# Just for historical purposes
import random

from app import db
from app.models import Attitude, Skill, SkillTypes, User, SeekerProfile, SeekerAttitude, SeekerSkill, SkillLevels, \
    CompanyProfile, JobPost, ImportanceLevel, JobPostSkill, JobPostAttitude

from resources.generators.attribute_gen import values, tech_skills, biz_skills, gen_values, gen_biz, gen_tech
from resources.generators.jobpost_gen import generate_jobpost

####
#### NOTE: Commented out functions are here for historical / reference purposes.
#### Nothing in here is supposed to be executed more than once!
####

# def load_attributes():
#     ## LOADED!
#     for v in values:
#         # values are used interchangeably with attitudes
#         a = Attitude()
#         a.title = v
#         db.session.add(a)
#     for ts in tech_skills:
#         s = Skill()
#         s.title = ts
#         s.type = SkillTypes.t
#         db.session.add(s)
#     for bs in biz_skills:
#         s = Skill()
#         s.title = bs
#         s.type = SkillTypes.b
#         db.session.add(s)
#     db.session.commit()
#
#
# def load_rand_seeker_attributes():
#     ## LOADED!!
#     for u in SeekerProfile.query.all():
#         uid = u.id
#         # generate some biz and tech skills
#         for biz, info in gen_biz((1, 4)).items():
#             lvl = info['level']
#             sid = Skill.query.filter_by(title=biz).first().id
#             seek_skl = SeekerSkill(seeker_id=uid, skill_id=sid, skill_level=SkillLevels(lvl))
#             db.session.add(seek_skl)
#         for tch, info in gen_tech((3, 8)).items():
#             lvl = info['level']
#             sid = Skill.query.filter_by(title=tch).first().id
#             seek_skl = SeekerSkill(seeker_id=uid, skill_id=sid, skill_level=SkillLevels(lvl))
#             db.session.add(seek_skl)
#         # generate some values/attitudes
#         for v in gen_values((2, 6)):
#             vid = Attitude.query.filter_by(title=v).first().id
#             seek_att = SeekerAttitude(seeker_id=uid, attitude_id=vid)
#             db.session.add(seek_att)
#     db.session.commit()
#
# def load_rand_jobposts():
#     ## LOADED!!
#     for c in CompanyProfile.query.all():
#         for _ in range(random.randint(1, 4)):
#             data = generate_jobpost(c.name, c.city, c.state, c.website)
#             post = JobPost(company_id=c.id, job_title=data['title'],
#                            city=data['location']['city'], state=data['location']['state'],
#                            description=data['description'],
#                            is_remote=data['remote'], active=data['active'],
#                            salary_min=data['salary']['min'], salary_max=data['salary']['max'],
#                            created_timestamp=data['creation']
#                            )
#             # need to add *and* commit so the id field will be populated.
#             # (needed to add skills/attitudes)
#             db.session.add(post)
#             db.session.commit()
#
#             for name, sdata in data['skills'].items():
#                 sid = Skill.query.filter_by(title=name).first().id
#                 slvl = sdata['experience']
#                 simp = sdata['importance']
#                 post_skl = JobPostSkill(jobpost_id=post.id, skill_id=sid,
#                                         skill_level_min=SkillLevels(slvl),
#                                         importance_level=ImportanceLevel(simp))
#                 db.session.add(post_skl)
#             for name, adata in data['attitudes'].items():
#                 aid = Attitude.query.filter_by(title=name).first().id
#                 aimp = adata['importance']
#                 post_att = JobPostAttitude(jobpost_id=post.id, attitude_id=aid,
#                                            importance_level=aimp)
#                 db.session.add(post_att)
#             db.session.commit()
