from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, \
    SubmitField
from wtforms.validators import Required, Length


class LogForm(FlaskForm):
    # name = StringField('Device name', validators=[Required(), Length(1, 64)])
    user = StringField('User name', validators=[Required(), Length(1, 64)])
    status = SelectField('Device status', coerce=int, choices=[(0, 'None'), (1, 'Normal'), (2, 'Broken')], default=0,
                         validators=[Required()])
    details = TextAreaField('Details')
    submit = SubmitField('Submit')
