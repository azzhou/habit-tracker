from flask_wtf import FlaskForm
from flask_login import current_user
from habit_tracker import bcrypt
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from habit_tracker.documents import User


class RegistrationForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(),
        EqualTo("password", message="Password doesn't match.")
    ])
    submit = SubmitField("Sign Up")

    # In-line validators to ensure fields aren't already taken
    def validate_email(self, email):
        if User.objects(email=email.data):
            raise ValidationError("That email is already taken.")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class UpdateEmailForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit_email = SubmitField("Update Email")

    # In-line validators to ensure fields aren't already taken
    def validate_email(self, email):
        if current_user.email != email.data and User.objects(email=email.data):
            raise ValidationError("That email is already taken.")


class UpdatePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired()])
    confirm_new_password = PasswordField("Confirm New Password", validators=[
        DataRequired(),
        EqualTo("new_password", message="New password doesn't match.")
    ])
    submit_password = SubmitField("Update Password")

    def validate_current_password(self, current_password):
        if not bcrypt.check_password_hash(current_user.password, current_password.data):
            raise ValidationError("Current password is incorrect.")

    def validate_new_password(self, new_password):
        if bcrypt.check_password_hash(current_user.password, new_password.data):
            raise ValidationError("New password cannot be the same as your current password.")
