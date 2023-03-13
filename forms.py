from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, IntegerField, RadioField, FloatField, DecimalField, PasswordField
from wtforms.validators import InputRequired, NumberRange, EqualTo, ValidationError, Length

class RegistrationForm(FlaskForm):
	username = StringField("Username: ", validators=[InputRequired(message="Username cannot be blank.")])
	password = PasswordField("Password: ", validators=[InputRequired(message="Password cannot be blank.")])
	password2 = PasswordField("Re-enter password: ", validators=[InputRequired(message="Password cannot be blank."), EqualTo('password', message="Passwords do not match")])
	submit = SubmitField("Submit")

class LoginForm(FlaskForm):
	username = StringField("Username: ", validators=[InputRequired(message="Username cannot be blank.")])
	password = PasswordField("Password: ", validators=[InputRequired(message="Password cannot be blank.")])
	submit = SubmitField("Submit")

class BuyForm(FlaskForm):
	quantity_buy = IntegerField("Volume: ", validators=[InputRequired(message="Minimum purchase quantity is 1.")])
	submit_buy = SubmitField("Buy")

class SellForm(FlaskForm):
	quantity_sell = IntegerField("Volume: ", validators=[InputRequired(message="0 stocks cannot be sold.")])
	submit_sell = SubmitField("Sell")

class AdminNewStockForm(FlaskForm):
	stockname = StringField("Stock Name: ", validators=[InputRequired(message="Stock name is missing.")])
	shorthand = StringField("Abbreviation: ", validators=[InputRequired(message="You must specify a 4 character shorthand."), Length(min=4, max=4, message="You must specify a 4 character shorthand.")])
	valuation = IntegerField("Initial Valuation: ", validators=[InputRequired(message="You must specify the initial valuation of the stock.")])
	share_count = IntegerField("Inital Share Count: ", validators=[InputRequired(message="Please enter the total share count"), NumberRange(min=1, message="Total share count must be greater than 0")])
	submit = SubmitField("Create")
