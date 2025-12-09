from flask import render_template, redirect, url_for, flash, request
from models.signup_model import SignupModel
import logging

logger = logging.getLogger(__name__)

class SignupController:
    def signup(self, form):
        if request.method == 'POST' and form.validate_on_submit():
            first_name = form.first_name.data
            last_name = form.last_name.data
            email = form.email.data
            password = form.password.data

            if SignupModel.email_exists(email):
                flash("Email đã tồn tại", "email_error")
                return render_template('signup/sign_up.html', form=form)

            SignupModel.create_user(first_name, last_name, email, password)
            flash("Successfully register, please log in", "success")
            return redirect(url_for('login'))

        return render_template('signup/sign_up.html', form=form)