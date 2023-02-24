from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, IntegerField, RadioField, FloatField, DecimalField, PasswordField
from wtforms.validators import InputRequired, NumberRange, EqualTo

class Form(FlaskForm):
    obj = StringField("Some label: ", validators=[InputRequired()])
    submit = SubmitField()

class RegistrationForm(FlaskForm):
	username = StringField("Username: ", validators=[InputRequired()])
	password = PasswordField("Password: ", validators=[InputRequired()])
	password2 = PasswordField("Re-enter password: ", validators=[InputRequired(), EqualTo('password')])
	submit = SubmitField("Submit")

class LoginForm(FlaskForm):
	username = StringField("Username: ", validators=[InputRequired()])
	password = PasswordField("Password: ", validators=[InputRequired()])
	submit = SubmitField("Submit")