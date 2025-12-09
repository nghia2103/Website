from flask import render_template, redirect, url_for, flash, request
from models.forgot_password_model import ForgotPasswordModel
import logging

logger = logging.getLogger(__name__)

class ForgotPasswordController:
    def forgot_password(self, form):
        if request.method == 'POST' and form.validate_on_submit():
            email = form.email.data
            if not ForgotPasswordModel.email_exists(email):
                flash("Email không tồn tại", "error")
                return render_template('signup/forgot_pass.html', form=form)
            flash("Succesfully sent email confirmation", "success")
            return redirect(url_for('login'))
        return render_template('signup/forgot_pass.html', form=form)