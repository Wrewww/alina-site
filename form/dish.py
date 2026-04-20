from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Optional

class DishForm(FlaskForm):
    name = StringField('название блюда', validators=[DataRequired()])
    total_weight = FloatField('вес готового блюда (г)', validators=[Optional()])
    submit = SubmitField('рассчитать КБЖУ')