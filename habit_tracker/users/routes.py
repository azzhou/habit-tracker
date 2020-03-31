from flask import Blueprint, render_template, redirect, url_for, flash
from habit_tracker.users.forms import RegistrationForm
from flask_login import current_user
from habit_tracker import bcrypt
from habit_tracker.models import User


users = Blueprint("users", __name__)


@users.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        flash("You are already logged in.", category="warning")
        return redirect(url_for("main.home"))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pass = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_pass
        )
        user.save()

        flash("Your account has been created!", category="success")
        return redirect(url_for("main.home"))
    return render_template("register.html", title="Register", form=form)
