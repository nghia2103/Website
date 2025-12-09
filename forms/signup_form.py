from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField
from wtforms.validators import DataRequired, Email, Length, Optional

class SignupForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(message="Vui lòng nhập tên"), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(message="Vui lòng nhập họ"), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(message="Vui lòng nhập email"), Email()])
    password = PasswordField('Password', validators=[DataRequired(message="Vui lòng nhập mật khẩu"), Length(min=6)])
    phone = StringField('Phone', validators=[Optional()])
    birthdate = DateField('Birthdate', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Submit')