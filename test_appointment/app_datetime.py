from flask import Flask, request, render_template, url_for, redirect
from flask_admin.form import DatePickerWidget
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, DateField, DateTimeField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo, DataRequired
from wtforms import ValidationError
import os
from datetime import datetime
from wtforms_components import TimeField

app = Flask(__name__)


class Config:
    SECRET_KEY = 'hard to guess string'

    @staticmethod
    def init_app(app):
        pass


config = Config()
app.config.from_object(config)

bootstrap = Bootstrap()
bootstrap.init_app(app)


class BookForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired()])
    photoset = SelectField('Set', choices=[('SET1', '1'), ('SET2', '2')])
    '''date = DateField('Appointment date', default='', validators=[DataRequired()], format='%Y/%m/%d',
                     widget=DatePickerWidget())'''
    # time = TimeField('Time', validators=[Required()], format="%H:%M")
    time = StringField('Time', validators=[Required()])
    '''date_time = DateTimeField('Time', validators=[Required()], format="%d%b%Y %H:%M",
                              default=datetime.utcnow)'''
    submit = SubmitField("Appoint")


@app.route('/datetime', methods=['GET', 'POST'])
def index():
    form = BookForm()
    if form.validate_on_submit():
        return form.time.data.strftime('%Y-%m-%d')
    return render_template('datetime.html', form=form)


if __name__ == '__main__':
    app.run()
