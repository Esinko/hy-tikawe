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
    api_change_password,
    api_delete_challenge,
    api_delete_submission,
    api_edit_challenge,
    api_edit_submission,
    api_login,
    api_post_challenge,
    api_post_submission,
    api_profile_edit,
    api_register,
    api_require_password_change,
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

# MARK: Before request
# If password change is required, only required routes are allowed
@app.before_request
def check_required_password_change():
    if (
        "user" in session and
        session["user"]["require_new_password"] and
        not session["user"]["is_admin"] and
        request.path not in ["/reset-password", "/api/change-password"] and
        not request.path.startswith("/public/") and
        not request.path.startswith("/a/")
    ):
        return redirect("/reset-password")
    
# Handle CSRF token for API endpoints
@app.before_request
def check_csrf():
    if request.path.startswith("/api/"):
        # API endpoints can only accept POST requests
        if request.method != "POST":
            return "Method not allowed.", 405
        
        # API endpoints require CSRF token in the form
        if "request_token" not in request.form.keys():
            return "Request token is required for API endpoints.", 401
        
        # Request token must match the one in the session
        if request.form["request_token"] != session["request_token"]:
            return "Invalid request token.", 401
        
        # If we reach this point, we are executing an API call
        # We want to expire the old request-token at this point
        session["request_token"] = token_urlsafe(16)
    elif "request_token" not in session:
        # Generate initial request token, if not present
        session["request_token"] = token_urlsafe(16)

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
    search_tab = ("users" if request.args.get("t") == "1" else "challenges")
    page = int(request.args.get("page") if "page" in request.args.keys() else "0")
    if not search_string:
        return "No search to perform.", 400
    
    users, challenges = [], []
    categories = get_db().get_categories()
    if search_tab == "users":
        users = get_db().search_users(search_string, page)
    else:
        challenges = get_db().search_challenges(search_string,
                                                       session["user"]["id"] if "user" in session else -1,
                                                       None,
                                                       page)
    return render_template("./search-results.html",
                           categories=categories,
                           challenges=challenges,
                           users=users,
                           search_string=search_string,
                           page=page,
                           top_text=get_random_top_text(),
                           tab=search_tab)

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

@app.get("/reset-password")
def reset_password():
    return render_template("./reset-password.html", top_text=get_random_top_text())
    

@app.get("/challenge-new")
def new_post():
    categories = get_db().get_categories()
    return render_template("./forms/challenge-new.html",
                           categories=categories,
                           top_text=get_random_top_text())

@app.route("/chall/<challenge_id>", defaults={"sub_path": "", "sub_action": "", "reply_id": ""})
@app.route("/chall/<challenge_id>/", defaults={"sub_path": "", "sub_action": "", "reply_id": ""})
@app.route("/chall/<string:challenge_id>/<path:sub_path>/", defaults={"sub_action": "", "reply_id": ""})
@app.route("/chall/<string:challenge_id>/<path:sub_path>/<string:reply_id>/<path:sub_action>")
def challenge(challenge_id, sub_path, reply_id, sub_action):
    categories = get_db().get_categories()
    user_id = session["user"]["id"] if "user" in session else -1
    try:
        # Get challenge data
        challenge = get_db().get_challenge(user_id, challenge_id)
    except ChallengeNotFoundException:
        return redirect("/")
    
    # Get comments and submissions or comment/submission to edit
    comments_and_submissions, reply_to_edit = ([], None)
    if not reply_id:
        comments_and_submissions = get_db().get_challenge_replies(user_id, challenge_id)
    elif sub_path == "com":
        reply_to_edit = get_db().get_comment(user_id, reply_id)
    elif sub_path == "sub":
        reply_to_edit = get_db().get_submission(user_id, reply_id)
    else:
        return "Unknown reply type.", 404

    # Default challenge template
    template = "./challenge.html"

    # If sub_path (and possibly sub_action), pick the proper form template
    if sub_path:
        form_key = sub_path + ("-" + sub_action if sub_action else "")
        forms = {
            "edit": "./forms/challenge-edit.html",
            "delete": "./forms/challenge-delete.html",
            "com-edit": "./forms/comment-edit.html",
            "com-delete": "./forms/comment-delete.html",
            "com": "./forms/comment-new.html",
            "sub-edit": "./forms/submission-edit.html",
            "sub-delete": "./forms/submission-delete.html",
            "sub": "./forms/submission-new.html"
        }
        if form_key not in forms:
            return "Not found.", 404
        template = forms[form_key]
    
    return render_template(template,
                           categories=categories,
                           challenge=challenge,
                           replies=comments_and_submissions,
                           reply_to_edit=reply_to_edit,
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

@app.route("/me/settings")
def user_settings():
    # Must be logged in
    if "user" not in session:
        redirect("/")
        return

    categories = get_db().get_categories()

    return render_template("./user-settings.html",
                           user=session["user"],
                           categories=categories,
                           top_text=get_random_top_text())

@app.get("/u/<username>")
def profile(username):
    categories = get_db().get_categories()
    page = int(request.args.get("page") if "page" in request.args.keys() else "0")
    try:
        # Get user data
        user = get_db().get_user(username)
    except UserNotFoundException:
        return redirect("/")
    
    content = get_db().get_user_content(session["user"]["id"] if "user" in session else -1,
                                                                        user.id, page)
    received_votes = get_db().get_received_votes(user.id)
    given_votes = get_db().get_given_votes(user.id)

    return render_template("./profile.html",
                           profile=user.profile.to_dict(),
                           username=username,
                           categories=categories,
                           content=content,
                           received_votes=received_votes,
                           given_votes=given_votes,
                           top_text=get_random_top_text(),
                           page=page)

@app.route("/u/<username>/settings")
def target_user_settings(username):
    # Must be logged in
    if "user" not in session:
        redirect("/")
        return
    
    # Must be admin
    if not session["user"]["is_admin"]:
        return "Permission denied.", 401
    
    # Get user
    user = get_db().get_user(username)
    print(user.to_dict())

    return render_template("./user-settings.html", user=user)

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
app.add_url_rule("/api/post/submission", view_func=api_post_submission, methods=["POST"])
app.add_url_rule("/api/edit/submission", view_func=api_edit_submission, methods=["POST"])
app.add_url_rule("/api/delete/submission", view_func=api_delete_submission, methods=["POST"])
app.add_url_rule("/api/change-password", view_func=api_change_password, methods=["POST"])
app.add_url_rule("/api/admin/request-password-change", view_func=api_require_password_change, methods=["POST"])
