from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, BooleanField, IntegerField, TextAreaField, Form, FieldList, \
    FormField
from wtforms.validators import DataRequired, Optional

from app.constants import STATE_ABBVS
from app.models import SkillLevels, ImportanceLevel
from resources.generators import SKILL_NAMES, ATTITUDE_NAMES


# TODO forms needed for editing profile, searching, messaging, etc.


class SkillRequirementForm(Form):
    skill = SelectField('Skill', coerce=str, choices=[""] + sorted(SKILL_NAMES))
    min_lvl = SelectField('Min. level', coerce=str, choices=[(i + 1, lvl.title())
                                                             for i, lvl in enumerate(SkillLevels.__members__.keys())])
    importance = SelectField('Importance', coerce=str, choices=[(i + 1, imp.title())
                                                                for i, imp in
                                                                enumerate(ImportanceLevel.__members__.keys())])


class AttitudeRequirementForm(Form):
    att = SelectField('Attitude', coerce=str, choices=[""] + sorted(ATTITUDE_NAMES))
    importance = SelectField('Importance', coerce=str, choices=[(i, imp.title())
                                                                for i, imp in
                                                                enumerate(ImportanceLevel.__members__.keys())])


class FlexibleIntegerField(IntegerField):
    def process_formdata(self, valuelist):
        """ valuelist is a list of string values representing the data in the form """
        if valuelist:  # something provided
            valuelist[0] = valuelist[0].replace(",", "")
        return super(FlexibleIntegerField, self).process_formdata(valuelist)


class WorkTypeField(Form):
    full_time = BooleanField('Full Time')
    part_time = BooleanField('Part Time')
    contract = BooleanField('Contract')


class JobPostForm(FlaskForm):
    active = BooleanField('Active', default=True)
    title = StringField('Job Title', validators=[DataRequired()])
    city = StringField('City')
    state = SelectField('State', choices=[""] + STATE_ABBVS)
    work_types = FormField(WorkTypeField)
    remote = BooleanField('Remote')
    salary_min = FlexibleIntegerField('Min. Salary', validators=[Optional()])
    salary_max = FlexibleIntegerField('Max. Salary', validators=[Optional()])
    description = TextAreaField('Description', default="")
    req_skills = FieldList(FormField(SkillRequirementForm), min_entries=0, max_entries=None)
    req_attitudes = FieldList(FormField(AttitudeRequirementForm), min_entries=0, max_entries=None)
    submit = SubmitField('Post it!')
