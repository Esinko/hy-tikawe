from flask import Flask, Response, redirect, render_template, send_from_directory, session
from api import api_delete_challenge, api_edit_challenge, api_login, api_post_challenge, api_profile_edit, api_register, api_vote
from database.params import database_params
from database.abstract import AbstractDatabase, AssetNotFoundException, ChallengeNotFoundException, DatabaseConnection, UserNotFoundException
from datetime import datetime
from util.filetype import filename_to_file_type

# Initialize database
database_connection = DatabaseConnection(*database_params).open()
database_connection.close()

# Initialize Flask
app = Flask(__name__)
app.secret_key = "TOTALLY_SECRET_KEY"

# MARK: Filters
@app.template_filter("epoch_to_date")
def epoch_to_date_filter(epoch):
    return datetime.fromtimestamp(epoch).strftime("%H:%M %d.%m.%Y")

# Public dir route
@app.route("/public/<path>")
def public(path):
    return send_from_directory("public", path)

# MARK: Pages
@app.route("/")
def home():
    database = AbstractDatabase(DatabaseConnection(*database_params).open())
    categories = database.get_categories()
    challenges = database.get_challenges(session["user"]["id"] if "user" in session else -1 , None, 0)
    database.connection.close()
    return render_template("./home.html", categories=categories, challenges=challenges)

@app.route("/login")
def login():
    return render_template("./login.html")

@app.route("/register")
def register():
    return render_template("./register.html")

@app.get("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.get("/challenge-new")
def new_post():
    database = AbstractDatabase(DatabaseConnection(*database_params).open())
    categories = database.get_categories()
    database.connection.close()
    return render_template("./challenge-new.html", categories=categories)

@app.route("/chall/<challenge_id>", defaults={"subpath": ""})
@app.route("/chall/<challenge_id>/<path:subpath>")
def challenge(challenge_id, subpath):
    database = AbstractDatabase(DatabaseConnection(*database_params).open())
    categories = database.get_categories()
    try:
        challenge = database.get_challenge(session["user"]["id"] if "user" in session else -1, challenge_id)
        database.connection.close()
        
        # Select template based on subpath
        template = "./challenge.html"
        if subpath == "edit":
            template = "./challenge-edit.html"
        elif subpath == "delete":
            template = "./challenge-delete.html"
        return render_template(template, categories=categories, challenge=challenge)
    except ChallengeNotFoundException:
        database.connection.close()
        return redirect("/")
    except Exception as err:
        database.connection.close()
        print("ERR", err)
        return "Internal Server Error.", 500

@app.get("/me")
def profile_me():
    return profile(session["user"]["username"])

@app.get("/me/edit")
def profile_edit():
    database = AbstractDatabase(DatabaseConnection(*database_params).open())
    categories = database.get_categories()
    user = database.get_user(session["user"]["username"])
    database.connection.close()
    return render_template("./profile-edit.html", profile=user.__dict__()["profile"], username=user.username, categories=categories)

@app.get("/u/<username>")
def profile(username):
    database = AbstractDatabase(DatabaseConnection(*database_params).open())
    categories = database.get_categories()
    try:
        user = database.get_user(username)
        database.connection.close()
    except UserNotFoundException:
        return redirect("/")
    return render_template("./profile.html", profile=user.__dict__()["profile"], username=username, categories=categories)

@app.get("/a/<id>")
def asset(id):
    database = AbstractDatabase(DatabaseConnection(*database_params).open())
    try:
        asset = database.get_asset(id)
        database.connection.close()
    except AssetNotFoundException:
        return redirect("/")

    response = Response(asset.value)
    response.headers["Content-Type"] = filename_to_file_type(asset.filename)
    return response

# MARK: API
app.add_url_rule("/api/login", view_func=api_login, methods=["POST"])
app.add_url_rule("/api/register", view_func=api_register, methods=["POST"])
app.add_url_rule("/api/profile/edit", view_func=api_profile_edit, methods=["POST"])
app.add_url_rule("/api/post/challenge", view_func=api_post_challenge, methods=["POST"])
app.add_url_rule("/api/edit/challenge", view_func=api_edit_challenge, methods=["POST"])
app.add_url_rule("/api/delete/challenge", view_func=api_delete_challenge, methods=["POST"])
app.add_url_rule("/api/vote/<type>/<target_id>", view_func=api_vote, methods=["POST"])
