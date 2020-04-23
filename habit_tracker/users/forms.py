from flask_wtf import FlaskForm
from flask_login import current_user
from habit_tracker import bcrypt
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import (DataRequired, Length, Email, EqualTo,
                                Regexp, ValidationError)
from habit_tracker.documents import User


class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[
        DataRequired(),
        Length(min=3, max=20, message="Username must be between 3 and 20 characters long."),
        Regexp(regex="^\\w+$", message="Username must contain alphanumeric characters only.")
    ])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(),
        EqualTo("password", message="Password doesn't match.")
    ])
    submit = SubmitField("Sign Up")

    # In-line validators to ensure fields aren't already taken
    def validate_username(self, username):
        if User.objects(username=username.data):
            raise ValidationError("That username is already taken.")

    def validate_email(self, email):
        if User.objects(email=email.data):
            raise ValidationError("That email is already taken.")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class UpdateBasicInfoForm(FlaskForm):
    username = StringField("Username", validators=[
        DataRequired(),
        Length(min=3, max=20, message="Username must be between 3 and 20 characters long."),
        Regexp(regex="^\\w+$", message="Username must contain alphanumeric characters only.")
    ])
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit_info = SubmitField("Update")

    # In-line validators to ensure fields aren't already taken
    def validate_username(self, username):
        if current_user.username != username.data and User.objects(username=username.data):
            raise ValidationError("That username is already taken.")

    def validate_email(self, email):
        if current_user.email != email.data and User.objects(email=email.data):
            raise ValidationError("That email is already taken.")


class UpdateAccountPasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired()])
    confirm_new_password = PasswordField("Confirm New Password", validators=[
        DataRequired(),
        EqualTo("new_password", message="New password doesn't match.")
    ])
    submit_password = SubmitField("Change Password")

    def validate_current_password(self, current_password):
        if not bcrypt.check_password_hash(current_user.password, current_password.data):
            raise ValidationError("Current password is incorrect.")

    def validate_new_password(self, new_password):
        if bcrypt.check_password_hash(current_user.password, new_password.data):
            raise ValidationError("New password cannot be the same as your current password.")
