from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import (DataRequired, Length, Email, EqualTo,
                                Regexp, ValidationError)
from habit_tracker.models import User


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
