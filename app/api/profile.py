from werkzeug.datastructures import ImmutableMultiDict

from app.api.users import edit_seeker, reset_seeker, update_seeker_skill, add_seeker_attitude, remove_seeker_skill, \
    remove_seeker_attitude, add_seeker_education, add_seeker_job, edit_company
from app.models import SeekerProfile, WorkTypes, Skill, Attitude, CompanyProfile


## [FOR SEEKER]
# form = ImmutableMultiDict([
#     ('firstName', 'David'), ('lastName', 'Myers'), ('phone', '4056136994'),
#     ('tagline', '...'), ('aboutMe', '...'),
#     ('eduexp-x-school', 'Soto University'), ('eduexp-x-field', 'Information Technology'), ('eduexp-x-degree', '#'),
#     ('jobexp-x-title', 'Network Security Engineer'), ('jobexp-x-years', '#'),
#     ('skill-x-lvl', '#'), ('skill-x-title', 'Apache HBase'),
#     ('attitude-x-title', 'Interpersonal motivation'),
#     ('deactivate', '1'), ('reactivate', '1')])
#
# files = ImmutableMultiDict([
#     ('profilePicFile', <FileStorage: '8bitself_head.png' ('image/png')>),
#     ('resumeFile', <FileStorage: 'parallel_AL_models.pdf' ('application/pdf')>)])

# edit_seeker(seeker_id,
#                 first_name: str = None, last_name: str = None,
#                 phone_number: str = None,
#                 city: str = None, state: str = None,
#                 work_wanted: WorkTypes = None, remote_wanted: bool = False,
#                 resume: bin = None
def update_seeker(seeker: SeekerProfile, form: ImmutableMultiDict, files: ImmutableMultiDict):
    # update User information
    if 'deactivate' in form:
        seeker._user.is_active = False
    elif 'reactivate' in form:
        seeker._user.is_active = True

    # update basic Profile information
    if 'resumeFile' in files:
        file = files['resumeFile']
        resume = file.read()
    else:
        resume = None

    edit_kwargs = {
        'first_name': form.get('firstName'),
        'last_name': form.get('lastName'),
        'phone_number': form.get('phone'),
        'city': form.get('city'),
        'state': form.get('state'),
        'work_wanted': WorkTypes(sum(i for i in form.getlist('worktype', type=int))),
        'remote_wanted': 'remote' in form,
        'tagline': form.get('tagline', ''),
        'summary': form.get('aboutMe', ''),
        'resume': resume
    }
    edit_seeker(seeker.id, **edit_kwargs)

    # convert form's skills to a more usable format
    new_skills = dict()  # map skill IDs to new skill level
    for s in range(form.get('max_count_skills', type=int)):
        key = f'skill-{s}-title'
        if key in form:
            sid = Skill.query.filter_by(title=form.get(key)).first().id
            level = form.get(f'skill-{s}-lvl', type=int)
            new_skills[sid] = level
    # now process skills based on what seeker currently does/does not have
    for ss in seeker._skills:  # ss=SeekerSkill object
        if ss.skill_id not in new_skills:
            remove_seeker_skill(seeker.id, ss.skill_id)
    for sid, slvl in new_skills.items():
        update_seeker_skill(seeker.id, sid, slvl)

    # convert form's attitudes to a more usable format
    new_attitudes = set()  # no mapping needed
    for s in range(form.get('max_count_attitudes', type=int)):
        key = f'attitude-{s}-title'
        if key in form:
            aid = Attitude.query.filter_by(title=form.get(key)).first().id
            new_attitudes.add(aid)
    # process attitudes based on what seeker currently does/does not have
    for sa in seeker._attitudes:  # sa = SeekerAttitude object
        if sa.attitude_id not in new_attitudes:
            remove_seeker_attitude(seeker.id, sa.attitude_id)
    for aid in new_attitudes:
        add_seeker_attitude(seeker.id, aid)

    # for past experiences, just delete everything and set again
    reset_seeker(seeker.id, skills=False, attitudes=False, jobs=True, educations=True)

    n_edus = form.get('max_count_eduexps', type=int)
    for s in range(n_edus):
        key = f'eduexp-{s}-school'
        if key in form:
            school = form.get(key)
            field = form.get(f'eduexp-{s}-field')
            level = form.get(f'eduexp-{s}-degree', type=int)
            add_seeker_education(seeker.id, school, level, field)

    n_jobs = form.get('max_count_jobexps', type=int)
    for s in range(n_jobs):
        key = f'jobexp-{s}-title'
        title = form.get(key)
        years = form.get(f'jobexp-{s}-years', type=int)
        if key in form:
            add_seeker_job(seeker.id, title, years)

# [COMPANY]
# form = ImmutableMultiDict([('name', 'company'), ('website', ''), ('city', ''), ('state', ''),
# ('tagline', ''), ('summary', ''), ('submit', '')])
# files = ImmutableMultiDict([('bannerFile', <FileStorage: 'gradiant.png' ('image/png')>), ('logoFile', <FileStorage: '8bitself_head.png' ('image/png')>)])
# edit_company(company_id,
#              name=None, city=None, state=None, website=None,
#              tagline=None, summary=None):
def update_company(company: CompanyProfile, form: ImmutableMultiDict, files: ImmutableMultiDict):
    edit_company(company.id,
                 name=form.get('name'), city=form.get('city'), state=form.get('state'),
                 website=form.get('website'),
                 tagline=form.get('tagline'), summary=form.get('summary'))
