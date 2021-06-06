from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.utils import secure_filename

from app.api.users import edit_seeker
from app.models import SeekerProfile, WorkTypes


## [FOR COMPANY]
# form = ImmutableMultiDict([('name', 'company'), ('website', ''), ('city', ''), ('state', ''), ('tagline', ''), ('summary', ''), ('submit', '')])
# files = ImmutableMultiDict([('bannerFile', <FileStorage: 'gradiant.png' ('image/png')>), ('logoFile', <FileStorage: '8bitself_head.png' ('image/png')>)])
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
        'work_wanted': WorkTypes(sum(i for i in form.getlist('worktype', int))),
        'remote_wanted': 'remote' in form,
        'resume': resume
    }
    edit_seeker(seeker.id, **edit_kwargs)
