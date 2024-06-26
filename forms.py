from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, IntegerField, RadioField, FloatField, DecimalField, PasswordField
from wtforms.validators import InputRequired, NumberRange, EqualTo, ValidationError, Length

class RegistrationForm(FlaskForm):
	username = StringField("Username: ", validators=[InputRequired(message="Username cannot be blank."), Length(0,30, message="Username is too long")])
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
	stockname = StringField("Stock Name: ", validators=[InputRequired(message="Stock name is missing."),Length(0,30, message="Stock name too long")])
	shorthand = StringField("Abbreviation: ", validators=[InputRequired(message="You must specify a 4 character shorthand."), Length(min=4, max=4, message="You must specify a 4 character shorthand")])
	valuation = IntegerField("Initial Valuation: ", validators=[InputRequired(message="You must specify the initial valuation of the stock."), NumberRange(min=0.000001,message="Value cannot be negative")])
	share_count = IntegerField("Inital Share Count: ", validators=[InputRequired(message="Please enter the total share count"), NumberRange(min=1, message="Total share count must be greater than 0")])
	submit = SubmitField("Create")

class GambleForm(FlaskForm):
	limit = IntegerField("Numbers to choose from: ", validators=[InputRequired(message="Please specify the highest number possible to be drawn."), NumberRange(min=2, message="2 is the minimum.")])
	guess = IntegerField("Guess: ", validators=[InputRequired(message="Please bet on a number!")])
	bet = IntegerField("Bet: ", validators=[InputRequired(message="Please gamble some money!")])
	submit = SubmitField("Gamble")