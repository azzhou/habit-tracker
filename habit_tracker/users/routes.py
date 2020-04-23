from flask import Blueprint, render_template, redirect, url_for, flash
from habit_tracker.users.forms import (RegistrationForm, LoginForm,
                                       UpdateEmailForm, UpdatePasswordForm)
from flask_login import current_user, login_user, logout_user, login_required
from habit_tracker import bcrypt
from habit_tracker.documents import User


users = Blueprint("users", __name__)


@users.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        flash("You are already logged in.", category="info")
        return redirect(url_for("main.home"))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pass = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            email=form.email.data,
            password=hashed_pass
        )
        user.save()
        flash("Your account has been created!", category="success")
        return redirect(url_for("users.login"))
    return render_template("register.html", title="Register", form=form)


@users.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        flash("You are already logged in.", category="info")
        return redirect(url_for("main.home"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.objects(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash(f"Welcome back!", category="info")
            return redirect(url_for('main.home'))
        else:
            flash("Login unsuccessful. Please check email and password.", category="danger")
    return render_template("login.html", title="Login", form=form)


@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("users.login"))


@users.route("/account", methods=["GET", "POST"])
@login_required
def account():
    email_form = UpdateEmailForm()
    password_form = UpdatePasswordForm()
    anchor = ""

    # Check submit field's data because is_submitted() doesn't differentiate between forms
    if email_form.submit_email.data:
        if email_form.validate():
            current_user.email = email_form.email.data
            current_user.save()
            flash("Your email has been updated!", category="success")
            return redirect(url_for("users.account"))
        else:
            # Used to bring form into view using JS if there are validation errors
            anchor = "update-email"
    else:
        email_form.email.data = current_user.email

    # Check submit field's data because is_submitted() doesn't differentiate between forms
    if password_form.submit_password.data:
        if password_form.validate():
            hashed_pass = bcrypt.generate_password_hash(password_form.new_password.data).decode('utf-8')
            current_user.password = hashed_pass
            current_user.save()
            flash("Your password has been updated!", category="success")
            return redirect(url_for("users.account"))
        else:
            # Used to bring form into view using JS if there are validation errors
            anchor = "update-password"

    return render_template("account.html",
                           title="Account",
                           email_form=email_form,
                           password_form=password_form,
                           anchor=anchor)


@users.route("/delete_account", methods=["POST"])
@login_required
def delete_account():
    current_user.delete()
    flash(f"Your account has been deleted!", category="success")
    return redirect(url_for("users.register"))
