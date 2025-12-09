from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(message="Vui lòng nhập email"), Email()])
    submit = SubmitField('Reset Password')