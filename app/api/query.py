from typing import Tuple
from app.models import SeekerProfile

# for u, a in session.query(User, Address). \
#         ...                     filter(User.id==Address.user_id). \
#         ...                     filter(Address.email_address=='jack@google.com'). \
#         ...                     all():


def request_args_to_kwargs(req_args):
    kwargs = dict()
    arg_worktype = req_args.get('worktype', '')
    if arg_worktype.isdigit():
        binstr = bin(int(arg_worktype))
        kwargs['worktype'] = [b == '1' for b in binstr[-3:]]

    if 'remote' in req_args:
        kwargs['remote'] = True

    arg_eduexp = req_args.get('eduexp', '')
    if len(arg_eduexp) == 2 and arg_eduexp.isdigit():
        kwargs['edu_range'] = [int(arg_eduexp[0]), int(arg_eduexp[1])]

    arg_workexp = req_args.get('workexp', '')
    if len(arg_workexp) == 2 and arg_workexp.isdigit():
        kwargs['work_range'] = [int(arg_workexp[0]), int(arg_workexp[1])]

    arg_dist = req_args.get('dist', '')
    if arg_dist and arg_dist.count('-') == 2:
        d, c, s = arg_dist.split("-")
        kwargs['loc_distance'] = int(d)
        kwargs['loc_citystate'] = [c, s]

    arg_tech = req_args.get('tech', '')
    if arg_tech.isdigit():
        kwargs['tech_skills'] = int(arg_tech)

    arg_biz = req_args.get('biz', '')
    if arg_biz.isdigit():
        kwargs['biz_skills'] = int(arg_biz)

    arg_att = req_args.get('att', '')
    if arg_att.isdigit():
        kwargs['atts'] = int(arg_att)
    return kwargs


def get_seeker_query(
        worktype: Tuple[bool, bool, bool] = None, remote: bool = None,
        edu_range: Tuple[int, int] = None, work_range: Tuple[int, int] = None,
        loc_distance: int = None, loc_citystate: Tuple[str, str] = None,
        tech_skills: int = None, biz_skills: int = None, atts: int = None):
    """
    Performs a search query on the seekers based on the provided filters.
    Returns a 'query' object that can then be passed to 'paginate'.
    """
    # Couldn't figure out how to convert some of these filters to pure SQL
    #   (necessary as part of the 'hybrid_property'/'hybrid_method' annotations to be used in calls to a query's
    #   'filter' call),
    #   so the entire list of seekers is queried as a Python list, then filtered thru Python's built-in function.
    #
    # To make this work with `paginate`, it needs to be a query, so the seeker objects left at the end of the filter
    #   are then converted to their IDs for querying the "proper" way.
    #

    matches = SeekerProfile.query.all()

    if worktype is not None and any(worktype):
        bin_worktype = sum(v << i for i, v in enumerate(worktype[::-1]))
        matches = filter(lambda m: m.work_wanted & bin_worktype > 0, matches)
    if remote is not None and remote:
        matches = filter(lambda m: m.remote_wanted == remote, matches)
    if edu_range is not None:
        matches = filter(lambda m: edu_range[0] <= m.min_edu_level <= edu_range[1], matches)
    if work_range is not None:
        matches = filter(lambda m: work_range[0] <= m.years_job_experience <= work_range[1], matches)
    if loc_distance is not None and loc_citystate is not None:
        matches = filter(lambda m: m.is_within(loc_distance, *loc_citystate), matches)
    if tech_skills is not None:
        matches = filter(lambda m: tech_skills & m.encode_tech_skills > 0, matches)
    if biz_skills is not None:
        matches = filter(lambda m: biz_skills & m.encode_biz_skills > 0, matches)
    if atts is not None:
        matches = filter(lambda m: atts & m.encode_attitudes > 0, matches)

    # This is the "right" way to use the filter command if someone knows how to set it up the proper way.
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

    match_ids = [m.id for m in matches]
    q = SeekerProfile.query.filter(SeekerProfile.id.in_(match_ids))
    return q
