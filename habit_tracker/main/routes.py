from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user


main = Blueprint("main", __name__)


@main.route("/")
@main.route("/home/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("habits.habit_list"))
    else:
        return render_template("home.html")
