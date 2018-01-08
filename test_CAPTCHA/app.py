from flask import Flask, request, render_template, url_for, redirect
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
import pygeoip
import os
from werkzeug.contrib.fixers import ProxyFix


ip_data_path = os.path.abspath(r"GeoIP/GeoIP.dat")
GEOIP = pygeoip.GeoIP(ip_data_path, pygeoip.MEMORY_CACHE)


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)


class Config:
    SECRET_KEY = 'hard to guess string'
    RECAPTCHA_PUBLIC_KEY = '6LdIRz8UAAAAAJYJRrZuKDlRQTehaRE9uTcVsO9A'
    RECAPTCHA_PRIVATE_KEY = '6LdIRz8UAAAAAOjNSx8JsZtZtpdTMRyWelAvYSIY'
    # RECAPTCHA_PARAMETERS = {'hl': 'zh', 'render': 'explicit'}
    # RECAPTCHA_DATA_ATTRS = {'theme': 'dark'}
    TESTING = False  # set app['TESTING'] to true for disabling reCaptcha

    @staticmethod
    def init_app(app):
        pass


config = Config()
app.config.from_object(config)

bootstrap = Bootstrap()
bootstrap.init_app(app)


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    password = PasswordField('Password', validators=[Required()])
    recaptcha = RecaptchaField()
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')


@app.route('/', methods=['GET', 'POST'])
def index():
    form = LoginForm()
    script = None
    if request.method == 'POST':
        ip = request.remote_addr
        # print(ip)
        country = GEOIP.country_name_by_addr(ip)
        if country == 'China' or '127.0.0.1':
            script = True
            return render_template('index.html', form=form, script=script)
    return render_template('index.html', form=form, script=script)


if __name__ == '__main__':
    app.run()
