from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

## TODO forms needed for editing profile, searching, messaging, etc.

class JobPostForm(FlaskForm): ## TODO expand me
    title = StringField('Job Title', validators=[DataRequired()])
    submit = SubmitField('Post it!')
