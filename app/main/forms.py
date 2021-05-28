from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, BooleanField, IntegerField, TextAreaField, Form, FieldList, \
    FormField
from wtforms.validators import DataRequired

## TODO forms needed for editing profile, searching, messaging, etc.

from app.constants import STATE_CHOICES, STATE_ABBVS
from app.models import SkillLevels, ImportanceLevel
from resources.generators import SKILL_NAMES, ATTITUDE_NAMES


class SkillRequirementForm(Form):
    skill = SelectField('Skill', choices=[""]+sorted(SKILL_NAMES))
    min_lvl = SelectField('Min. level', choices=[(i+1, lvl.title())
                                                 for i, lvl in enumerate(SkillLevels.__members__.keys())])
    importance = SelectField('Importance', choices=[(i+1, imp.title())
                                                    for i, imp in enumerate(ImportanceLevel.__members__.keys())])


class AttitudeRequirementForm(Form):
    att = SelectField('Attitude', choices=["Choose..."]+sorted(ATTITUDE_NAMES))
    importance = SelectField('Importance', choices=[(i, imp.title())
                                                    for i, imp in enumerate(ImportanceLevel.__members__.keys())])


class JobPostForm(FlaskForm): ## TODO expand me
    title = StringField('Job Title', validators=[DataRequired()])
    city = StringField('City')
    state = SelectField('State', choices=STATE_ABBVS)
    remote = BooleanField('Remote')
    salary_min = IntegerField('Min. Salary', default=0)
    salary_max = IntegerField('Max. Salary', default=0)
    description = TextAreaField('Description')
    req_skills = FieldList(FormField(SkillRequirementForm), min_entries=0, max_entries=None)
    req_attitudes = FieldList(FormField(AttitudeRequirementForm), min_entries=0, max_entries=None)
    submit = SubmitField('Post it!')
