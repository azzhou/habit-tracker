from flask import Blueprint, render_template

errors = Blueprint("errors", __name__)


@errors.app_errorhandler(404)
def error_404(error):
    print(error)
    error_title = "Page not found (404)"
    error_text = "That page does not exist."
    return render_template("error.html", error_title=error_title, error_text=error_text), 404


@errors.app_errorhandler(500)
def error_500(error):
    error_title = "This page isn't working (500)"
    error_text = "We're experiencing an error on our end. Please try again later."
    return render_template("error.html", error_title=error_title, error_text=error_text), 500
