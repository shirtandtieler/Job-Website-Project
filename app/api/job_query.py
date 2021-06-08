import re
from typing import Tuple, List
from itertools import groupby

from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.urls import url_encode

from app.models import Skill, Attitude, JobPost, WorkTypes, MatchScores


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


def job_form_to_url_params(form: ImmutableMultiDict) -> str:
    """
    Converts the form results from a job search to the proper URL arguments.
    The keys in 'form' are based on the name attribute in the search HTML.
    The keys in the output are URL parameters, whose names are based on abbreviations of what they're searching for.
    """
    # --- use get(type=X)
    # lf_ft, lf_pt, lf_contract, lf_remote: 1 or ''
    # salary_lower, salary_upper: 0-200
    # dist_choice: True (any) or False (within)
    # dist_miles: int
    # dist_city: str
    # dist_state: str
    # techs, bizs, atts: list[int] --- use getlist(type=int)
    args = dict()
    args['worktype'] = form.get('lf_ft', '0') + form.get('lf_pt', '0') + form.get('lf_contract', '0') + form.get(
        'lf_remote', '0')
    args['salary'] = form.get('salary_lower', '0') + '-' + form.get('salary_upper', '200')
    if not form.get('dist_choice', type=int):
        # False = within the given distance
        args['dist'] = "-".join([form.get('dist_miles', '50'), form.get('dist_city'), form.get('dist_state')])

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

    print(f'URL ENCODED {form} TO {args}')
    return url_encode(args)


def job_url_args_to_input_states(req_args: ImmutableMultiDict) -> dict:
    """
    Converts the args passed in the request to a dictionary which the filter bar can set the states of its input to.
    The keys in 'req_args' are the URL parameters, whose names are based on abbreviations of what they're searching for.
    The keys in the output dictionary are based on the IDs in the filter panel.
    """
    options = dict()
    # set all defaults and override in the next sections
    options['lf_ft'] = options['lf_pt'] = options['lf_contract'] = options['lf_remote'] = 'checked'
    options['slider-salary'] = [0, 205]
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

    arg_salary = req_args.get('salary', '')
    if re.match(r'\d{1,3}-\d{1,3}', arg_salary):
        s0, s1 = arg_salary.split('-')
        options['slider-salary'] = [int(s0), int(s1)]

    arg_dist = req_args.get('dist', '')
    if arg_dist and arg_dist.count('-') == 2:
        d, c, s = arg_dist.split("-")
        options['dist_any'] = ''
        options['dist_within'] = 'checked'
        options['dist_miles'] = d
        options['dist_city'] = c
        options['dist_state'] = s

    arg_tech = req_args.get('tech', '')
    if arg_tech:
        options['sel_techs'] = _decompress(arg_tech)

    arg_biz = req_args.get('biz', '')
    if arg_biz:
        options['sel_bizs'] = _decompress(arg_biz)

    arg_att = req_args.get('att', '')
    if arg_att:
        options['sel_atts'] = _decompress(arg_att)

    print(f'INPUT SET {req_args} TO {options}')
    return options


def job_url_args_to_query_args(req_args: ImmutableMultiDict) -> dict:
    """
    Converts the args passed in the request to a dictionary which the job query function can process.
    The keys in 'req_args' are the URL parameters, whose names are based on abbreviations of what they're searching for.
    The keys in the output dictionary are based on the parameter names given to the `get_seeker_query` function.
    """
    kwargs = dict()
    arg_worktype = req_args.get('worktype', '')
    if arg_worktype.isdigit():
        binstr = bin(int(arg_worktype))
        kwargs['worktype'] = [b == '1' for b in binstr[-3:]]

    # # set as True unless explicitly set to 0
    # if req_args.get('remote', '') != '0':
    #     kwargs['remote'] = True

    arg_salary = req_args.get('salary', '')
    if re.match(r'\d{1,3}-\d{1,3}', arg_salary):
        s0, s1 = arg_salary.split('-')
        kwargs['sal_range'] = [int(s0)*1e3, int(s1)*1e3]
        # when salary range is 201k, that should be considered "> 200k"; adjust specific range values accordingly.
        # (when index 0 is 201k, that's fine since it's the lower bound,
        #   but when index 1 is 201k, that should be a large enough number ot capture those with 200k salaries)
        if kwargs['sal_range'][1] == 201e3:
            kwargs['sal_range'][1] = 1e9  # billion

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
    print(f'CONVERTED {req_args} TO {kwargs}')
    return kwargs


def get_job_query(
        worktype: Tuple[bool, bool, bool, bool] = None,
        sal_range: Tuple[int, int] = None,
        loc_distance: int = None, loc_citystate: Tuple[str, str] = None,
        tech_skills: int = None, biz_skills: int = None, atts: int = None,
        seeker_id: int = None):
    """
    Performs a search query on the jobs based on the provided filters.
    If seeker_id is passed results will be sorted by matching score, otherwise by date.
    Returns a 'query' object that can then be passed to 'paginate'.
    """

    matches = JobPost.query.all()

    # first, always filter out any non-active jobs
    matches = filter(lambda m: m.active, matches)
    # also filter out any jobs related to companies who are inactive
    matches = filter(lambda m: m._company._user.is_active, matches)

    if worktype is not None and any(worktype):
        bin_worktype = sum(v << i for i, v in enumerate(worktype[::-1]))
        # work wanted only has for the 3 types; add in remote before checking for truthiness
        matches = filter(lambda m: ((m.work_type or WorkTypes.any) << 1 | int(m.is_remote or False)) & bin_worktype > 0, matches)
    if sal_range is not None:
        # accept any that overlap in range.
        # since salaries may be None, default them to an appropriate extreme
        matches = filter(lambda m: (m.salary_min or 0) <= sal_range[1] and (m.salary_max or 1e9) >= sal_range[0], matches)
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
    q = JobPost.query.filter(JobPost.id.in_(match_ids))
    if seeker_id is not None:  # sort by matching score, then by time created
        q = q.join(MatchScores, JobPost.id == MatchScores.jobpost_id)\
            .filter(MatchScores.seeker_id == seeker_id)\
            .order_by(MatchScores.score.desc(), JobPost.created_timestamp.desc())
    else:  # fallback to sorting just by time created
        q = q.order_by(JobPost.created_timestamp.desc())
    return q
