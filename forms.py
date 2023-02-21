from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, IntegerField, RadioField, FloatField, DecimalField
from wtforms.validators import InputRequired, NumberRange

class Form(FlaskForm):
    obj = StringField("Some label: ", validators=[InputRequired()])
    submit = SubmitField()