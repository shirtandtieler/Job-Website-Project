from typing import Tuple
from app.models import SeekerProfile

# for u, a in session.query(User, Address). \
#         ...                     filter(User.id==Address.user_id). \
#         ...                     filter(Address.email_address=='jack@google.com'). \
#         ...                     all():


def get_seeker_query(
        worktype: Tuple[bool, bool, bool] = None, remote: bool = None,
        edu_range: Tuple[int, int] = None, work_range: Tuple[int, int] = None,
        loc_distance: int = None, loc_citystate: Tuple[str, str] = None,
        tech_skills: int = None, biz_skills: int = None, atts: int = None):
    q = SeekerProfile.query

    if worktype is not None and any(worktype):
        bin_worktype = sum(v << i for i, v in enumerate(worktype[::-1]))
        q = q.filter(SeekerProfile.work_wanted & bin_worktype > 0)
    if remote is not None and remote:
        q = q.filter(SeekerProfile.remote_wanted == remote)
    if edu_range is not None:
        q = q.filter(edu_range[0] <= SeekerProfile.min_edu_level <= edu_range[1])
    if work_range is not None:
        q = q.filter(work_range[0] <= SeekerProfile.years_job_experience <= work_range[1])
    if loc_distance is not None and loc_citystate is not None:
        q = q.filter(SeekerProfile.is_within(loc_distance, *loc_citystate))
    if tech_skills is not None:
        q = q.filter(tech_skills & SeekerProfile.encode_tech_skills > 0)
    if biz_skills is not None:
        q = q.filter(biz_skills & SeekerProfile.encode_biz_skills > 0)
    if atts is not None:
        q = q.filter(atts & SeekerProfile.encode_attitudes > 0)

    # q = q.filter(
    #     SeekerProfile.work_wanted & bin_worktype > 0,
    #     SeekerProfile.remote_wanted == remote,
    #     edu_range[0] <= SeekerProfile.min_edu_level() <= edu_range[1],
    #     work_range[0] <= SeekerProfile.years_job_experience() <= work_range[1],
    #     q_dist_func(SeekerProfile),
    #     tech_skills & SeekerProfile.encode_tech_skills > 0,
    #     biz_skills & SeekerProfile.encode_biz_skills > 0,
    #     atts & SeekerProfile.encode_attitudes > 0
    # )
    return q
