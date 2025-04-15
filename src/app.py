from pathlib import Path
from flask import (
    Flask,
    Response,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    g
)
from api import (
    api_delete_challenge,
    api_edit_challenge,
    api_login,
    api_post_challenge,
    api_profile_edit,
    api_register,
    api_vote,
    api_delete_comment,
    api_edit_comment,
    api_post_comment
)
from database.abstract import (
    AssetNotFoundException,
    ChallengeNotFoundException,
    UserNotFoundException
)
from datetime import datetime
from util.get_db import get_db
from util.filetype import filename_to_file_type
from util.random_text import get_random_top_text
from secrets import token_urlsafe

# Initialize Flask
app = Flask(__name__)

# Generate secret
secret_key = Path("./.secret")
if not secret_key.exists():
    secret_key.write_text(token_urlsafe(32))
app.secret_key = secret_key.read_text()

# MARK: Filters
@app.template_filter("epoch_to_date")
def epoch_to_date_filter(epoch):
    return datetime.fromtimestamp(epoch).strftime("%d.%m.%Y @ %H:%M ")

# MARK: DB teardown
@app.teardown_appcontext # Auto-closes the database connection
def close_connection(_):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

# Public dir route
@app.route("/public/<path>")
def public(path):
    return send_from_directory("public", path)

# MARK: Pages
@app.route("/")
@app.route("/c/<category_id>")
def home(category_id=None):
    page = int(request.args.get("page") if "page" in request.args.keys() else "0")
    categories = get_db().get_categories()
    challenges = get_db().get_challenges(
        session["user"]["id"] if "user" in session else -1,
        category_id,
        page)
    category_name = categories[int(category_id) - 1].name if category_id else None
    return render_template("./home.html",
                           at_home=request.path == "/",
                           categories=categories,
                           challenges=challenges,
                           category_name=category_name,
                           page=page,
                           top_text=get_random_top_text())

@app.route("/search")
def search():
    search_string = request.args.get("s")
    page = int(request.args.get("page") if "page" in request.args.keys() else "0")
    if not search_string:
        return "No search to perform.", 400
    categories = get_db().get_categories()
    challenges = get_db().search_challenge(search_string,
                                                       session["user"]["id"] if "user" in session else -1,
                                                       None,
                                                       page)
    return render_template("./search-results.html",
                           categories=categories,
                           challenges=challenges,
                           search_string=search_string,
                           page=page,
                           top_text=get_random_top_text())

@app.route("/login")
def login():
    return render_template("./login.html", top_text=get_random_top_text())

@app.route("/register")
def register():
    return render_template("./register.html", top_text=get_random_top_text())

@app.get("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.get("/challenge-new")
def new_post():
    categories = get_db().get_categories()
    return render_template("./forms/challenge-new.html",
                           categories=categories,
                           top_text=get_random_top_text())

@app.route("/chall/<challenge_id>", defaults={"subpath": "", "subaction": "", "reply_id": ""})
@app.route("/chall/<challenge_id>/", defaults={"subpath": "", "subaction": "", "reply_id": ""})
@app.route("/chall/<string:challenge_id>/<path:subpath>/", defaults={"subaction": "", "reply_id": ""})
@app.route("/chall/<string:challenge_id>/<path:subpath>/<string:reply_id>/<path:subaction>")
def challenge(challenge_id, subpath, reply_id, subaction):
    categories = get_db().get_categories()
    user_id = session["user"]["id"] if "user" in session else -1
    try:
        # Get challenge data
        challenge = get_db().get_challenge(user_id, challenge_id)
    except ChallengeNotFoundException:
        return redirect("/")
    
    # Get comments and submissions
    comments_and_submissions, comment_to_edit = ([], None)
    if not reply_id:
        comments_and_submissions = get_db().get_challenge_replies(user_id, challenge_id)
    else:
        comment_to_edit = get_db().get_comment(user_id, reply_id)

    # Select template based on subpath
    template = "./challenge.html"
    if subpath == "edit":
        template = "./forms/challenge-edit.html"
    elif subpath == "delete":
        template = "./forms/challenge-delete.html"
    elif subpath == "com" and subaction == "edit":
        template = "./forms/comment-edit.html"
    elif subpath == "com" and subaction == "delete":
        template = "./forms/comment-delete.html"
    elif subpath == "com":
        template = "./forms/comment-new.html"
    return render_template(template,
                           categories=categories,
                           challenge=challenge,
                           replies=comments_and_submissions,
                           comment_to_edit=comment_to_edit,
                           top_text=get_random_top_text())

@app.get("/me")
def profile_me():
    return profile(session["user"]["username"])

@app.get("/me/edit")
def profile_edit():
    categories = get_db().get_categories()
    user = get_db().get_user(session["user"]["username"])
    return render_template("./forms/profile-edit.html",
                           profile=user.profile.to_dict(),
                           username=user.username,
                           categories=categories,
                           top_text=get_random_top_text())

@app.get("/u/<username>")
def profile(username):
    categories = get_db().get_categories()
    try:
        # Get user data
        user = get_db().get_user(username)
    except UserNotFoundException:
        return redirect("/")
    
    content = get_db().get_user_content(session["user"]["id"] if "user" in session else -1,
                                                                        user.id)
    received_votes = get_db().get_received_votes(user.id)
    given_votes = get_db().get_given_votes(user.id)

    return render_template("./profile.html",
                           profile=user.profile.to_dict(),
                           username=username,
                           categories=categories,
                           content=content,
                           received_votes=received_votes,
                           given_votes=given_votes,
                           top_text=get_random_top_text())

@app.get("/a/<id>")
def asset(id):
    try:
        asset = get_db().get_asset(id)
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
app.add_url_rule("/api/post/comment", view_func=api_post_comment, methods=["POST"])
app.add_url_rule("/api/edit/comment", view_func=api_edit_comment, methods=["POST"])
app.add_url_rule("/api/delete/comment", view_func=api_delete_comment, methods=["POST"])
