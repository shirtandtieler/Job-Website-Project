import re
from typing import Tuple, List
from itertools import groupby

from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.urls import url_encode, url_decode

from app.models import SeekerProfile, Skill, Attitude, MatchScores


def _compress(indices: List[int], max_size: int) -> str:
    """
    Encodes a list of indices to a binary string, then compresses it.
    """
    bin_list = ['0' for _ in range(max_size)]  # the IDs start at 1
    for i in indices:
        bin_list[i - 1] = '1'
    bin_str = ''.join(bin_list)

    # Hex method: Works better when options chosen are > ~30
    # bin_int = int(bin_str, base=2)
    # return format(bin_int, 'x')

    # Compression method: 20-50% smaller than just hexing, but only for up to 30 options
    # The compressed string begins with the starting number (0 or 1),
    # followed by the number of repeats (in hex).
    # If the hex value is longer than 1 character, it's prefixed by a period.
    groups = groupby(bin_str)
    counts = [(label, sum(1 for _ in group)) for label, group in groups]
    output = counts[0][0]
    for _, count in counts:
        f = format(count, 'x')
        if len(f) > 1:
            f = "." + f
        output += f
    return output


def _decompress(cstr, output=None):
    """
    Decompresses the compressed attribute string to the given output type.
    Default method is to decompress to the list of IDs ("ids")
    Can also pass "int" to have it output as an integer representing the binary form.
    """
    bin_str = ""
    d, ptr, size = cstr[0], 1, 1
    while ptr < len(cstr):

        c = cstr[ptr:ptr + size]
        ptr += 1
        if c == '.':
            size = 2
            continue
        bin_str += d * int(c, base=16)

        # flip d between 0 and 1
        d = '1' if d == '0' else '0'
        # reset size
        if size == 2:
            size = 1
            ptr += 1
    if output == "int":
        return int(bin_str, base=2)
    return [i + 1 for i, v in enumerate(bin_str) if v == '1']  # add 1 to get ID


def seeker_form_to_url_params(form: ImmutableMultiDict, existing_query_str: str = None) -> str:
    """
    Converts the form results from a seeker search to the proper URL arguments.
    The keys in 'form' are based on the name attribute in the search HTML.
    Can pass an existing query_str to load the values from (mostly just used for updating job select in company search).
    The keys in the output are URL parameters, whose names are based on abbreviations of what they're searching for.
    """
    # --- use get(type=X)
    # job-select: # (Only for company users)
    # lf_ft, lf_pt, lf_contract, lf_remote: 1 or ''
    # edulvl_lower, edulvl_upper: 0-5
    # workyrs_lower, workyrs_upper: 0-11
    # dist_choice: True (any) or False (within)
    # dist_miles: int
    # dist_city: str
    # dist_state: str
    # techs, bizs, atts: list[int] --- use getlist(type=int)
    args = dict()

    arg_jselect = form.get('job-select', -1, type=int)  # ignore job select arg if it's -1
    if 'job-select' in form and arg_jselect > 0:
        args['sortby'] = form.get('job-select', type=int)
        if existing_query_str is not None and len(form) == 1:  # only want this to fire when POSTing from job select field
            existing_args = url_decode(existing_query_str)  # remove job select/sort by so it doesn't override
            _ = existing_args.pop('sortby', None)
            args.update(existing_args)
            return url_encode(args)

    args['worktype'] = form.get('lf_ft', '0') + form.get('lf_pt', '0') + form.get('lf_contract', '0') + form.get(
        'lf_remote', '0')
    args['eduexp'] = form.get('edulvl_lower', '0') + form.get('edulvl_upper', '5')
    # need to convert to int so that it can be converted to hex (since nums can go up to 11)
    args['workexp'] = format(form.get('workyrs_lower', 0, type=int), 'x') + \
                      format(form.get('workyrs_upper', 11, type=int), 'x')
    if not form.get('dist_choice', 1, type=int):
        # False = within the given distance
        args['dist'] = "-".join([form.get('dist_miles', '50'), form.get('dist_city', ''), form.get('dist_state', '')])

    tlist = form.getlist('techs', type=int)
    if tlist:
        tcmp = _compress(tlist, Skill.count())
        args['tech'] = tcmp
    blist = form.getlist('bizs', type=int)
    if blist:
        bcmp = _compress(blist, Skill.count())
        args['biz'] = bcmp
    alist = form.getlist('atts', type=int)
    if alist:
        acmp = _compress(alist, Attitude.count())
        args['att'] = acmp

    return url_encode(args)


def seeker_url_args_to_input_states(req_args: ImmutableMultiDict) -> dict:
    """
    Converts the args passed in the request to a dictionary which the filter bar can set the states of its input to.
    The keys in 'req_args' are the URL parameters, whose names are based on abbreviations of what they're searching for.
    The keys in the output dictionary are based on the IDs in the filter panel.
    """
    options = dict()
    # set all defaults and override in the next sections
    options['lf_ft'] = options['lf_pt'] = options['lf_contract'] = options['lf_remote'] = 'checked'
    options['slider-edulvl'] = [0, 5]
    options['slider-workyrs'] = [0, 11]
    options['dist_any'] = 'checked'
    options['dist_within'] = options['dist_miles'] = options['dist_city'] = options['dist_state'] = ''
    options['sel_techs'] = options['sel_bizs'] = options['sel_atts'] = []

    # work types/looking for section.
    arg_worktype = req_args.get('worktype', '')
    if arg_worktype:
        options['lf_ft'] = '' if arg_worktype[0] == '0' else options['lf_ft']
        options['lf_pt'] = '' if arg_worktype[1] == '0' else options['lf_pt']
        options['lf_contract'] = '' if arg_worktype[2] == '0' else options['lf_contract']
        options['lf_remote'] = '' if arg_worktype[3] == '0' else options['lf_remote']

    arg_eduexp = req_args.get('eduexp', '')
    if len(arg_eduexp) == 2 and arg_eduexp.isdigit():
        options['slider-edulvl'] = [int(arg_eduexp[0]), int(arg_eduexp[1])]

    arg_workexp = req_args.get('workexp', '')  # need to use regex since work can be up to 11
    if len(arg_workexp) == 2 and re.match("^[0-9A-F]{2}$", arg_workexp, re.I):
        options['slider-workyrs'] = [int(arg_workexp[0], base=16), int(arg_workexp[1], base=16)]

    arg_dist = req_args.get('dist', '')
    if arg_dist and arg_dist.count('-') == 2:
        d, c, s = arg_dist.split("-")
        options['dist_any'] = ''
        options['dist_within'] = 'checked'
        options['dist_miles'] = d
        options['dist_city'] = c
        options['dist_state'] = s

    arg_tech = req_args.get('tech', '')
    if arg_tech:  # TODO incorporate
        options['sel_techs'] = _decompress(arg_tech)
    # if arg_tech.isdigit():  # for when arg is an int
    #     kwargs['tech_skills'] = int(arg_tech)

    arg_biz = req_args.get('biz', '')
    if arg_biz:  # TODO incorporate
        options['sel_bizs'] = _decompress(arg_biz)
    # if arg_biz.isdigit():  # for when arg is an int
    #     kwargs['biz_skills'] = int(arg_biz)

    arg_att = req_args.get('att', '')
    if arg_att:
        options['sel_atts'] = _decompress(arg_att)

    return options


def seeker_url_args_to_query_args(req_args: ImmutableMultiDict) -> dict:
    """
    Converts the args passed in the request to a dictionary which the seeker query function can process.
    The keys in 'req_args' are the URL parameters, whose names are based on abbreviations of what they're searching for.
    The keys in the output dictionary are based on the parameter names given to the `get_seeker_query` function.
    """
    kwargs = dict()
    arg_postid = req_args.get('sortby', -1, type=int)
    if arg_postid >= 0:
        kwargs['jobpost_id'] = arg_postid

    arg_worktype = req_args.get('worktype', '')
    if arg_worktype.isdigit():
        binstr = bin(int(arg_worktype))
        kwargs['worktype'] = [b == '1' for b in binstr[-3:]]

    # # set as True unless explicitly set to 0
    # if req_args.get('remote', '') != '0':
    #     kwargs['remote'] = True

    arg_eduexp = req_args.get('eduexp', '')
    if len(arg_eduexp) == 2 and arg_eduexp.isdigit():
        kwargs['edu_range'] = [int(arg_eduexp[0]), int(arg_eduexp[1])]

    arg_workexp = req_args.get('workexp', '')  # need to use regex since work can be up to 11
    if len(arg_workexp) == 2 and re.match("^[0-9A-F]{2}$", arg_workexp, re.I):
        kwargs['work_range'] = [int(arg_workexp[0], base=16), int(arg_workexp[1], base=16)]
        # when work range is 11, should be considered "> 10"; adjust specific range values accordingly.
        # (when index 0 is 11, that's fine since it's the lower bound.
        #   but when index 1 is 11, should be a large number to capture those with 11+ years)
        if kwargs['work_range'][1] == 11:
            kwargs['work_range'][1] = 9999

    arg_dist = req_args.get('dist', '')
    if arg_dist and arg_dist.count('-') == 2:
        d, c, s = arg_dist.split("-")
        kwargs['loc_distance'] = int(d)
        kwargs['loc_citystate'] = [c, s]

    arg_tech = req_args.get('tech', '')
    if arg_tech:
        kwargs['tech_skills'] = _decompress(arg_tech, output="int")
    # if arg_tech.isdigit():  # for when arg is an int
    #     kwargs['tech_skills'] = int(arg_tech)

    arg_biz = req_args.get('biz', '')
    if arg_biz:
        kwargs['biz_skills'] = _decompress(arg_biz, output="int")
    # if arg_biz.isdigit():  # for when arg is an int
    #     kwargs['biz_skills'] = int(arg_biz)

    arg_att = req_args.get('att', '')
    if arg_att:
        kwargs['atts'] = _decompress(arg_att, output="int")
    # if arg_att.isdigit():  # for when arg is an int
    #     kwargs['atts'] = int(arg_att)
    return kwargs


def get_seeker_query(
        worktype: Tuple[bool, bool, bool, bool] = None,
        edu_range: Tuple[int, int] = None, work_range: Tuple[int, int] = None,
        loc_distance: int = None, loc_citystate: Tuple[str, str] = None,
        tech_skills: int = None, biz_skills: int = None, atts: int = None,
        jobpost_id: int = None):
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
    # first, always filter out any non-active jobs
    matches = filter(lambda m: m._user.is_active, matches)

    if worktype is not None and any(worktype):
        bin_worktype = sum(v << i for i, v in enumerate(worktype[::-1]))
        # work wanted only has for the 3 types; add in remote before checking for truthiness
        matches = filter(lambda m: (m.work_wanted << 1 | int(m.remote_wanted)) & bin_worktype > 0, matches)

        # old way below; filtered out remote when worktype was 1111
        # bin_worktype = sum(v << i for i, v in enumerate(worktype[-2::-1]))
        # matches = filter(lambda m: m.work_wanted & bin_worktype > 0, matches)
        # matches = filter(lambda m: m.remote_wanted == worktype[-1], matches)
    if edu_range is not None:
        matches = filter(lambda m: edu_range[0] <= m.min_edu_level <= edu_range[1], matches)
    if work_range is not None:
        matches = filter(lambda m: work_range[0] <= m.years_job_experience <= work_range[1], matches)
    if loc_distance is not None and loc_citystate is not None:
        matches = filter(lambda m: m.is_within(loc_distance, *loc_citystate), matches)
    if tech_skills is not None:
        matches = filter(lambda m: tech_skills & m.encode_tech_skills() > 0, matches)
    if biz_skills is not None:
        matches = filter(lambda m: biz_skills & m.encode_biz_skills() > 0, matches)
    if atts is not None:
        matches = filter(lambda m: atts & m.encode_attitudes() > 0, matches)
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
    if jobpost_id is not None:  # sort by matching score
        q = q.join(MatchScores, SeekerProfile.id == MatchScores.seeker_id) \
            .filter(MatchScores.jobpost_id == jobpost_id) \
            .order_by(MatchScores.score.desc())
    return q
