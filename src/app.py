from pathlib import Path
from datetime import datetime
from secrets import token_urlsafe
from traceback import print_exception
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
from werkzeug.exceptions import NotFound
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
    UserNotFoundException,
    page_size
)
from util.get_db import get_db
from util.filetype import filename_to_file_type
from util.random_text import get_random_top_text

# Initialize Flask
app = Flask(__name__)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Strict"

# Add custom functions to templates
app.jinja_env.globals["get_random_top_text"] = get_random_top_text
app.jinja_env.globals["get_categories"] = lambda: get_db().get_categories()
app.jinja_env.globals["get_page_size"] = lambda: page_size

# Generate secret
secret_key = Path("./.secret")
if not secret_key.exists():
    secret_key.write_text(token_urlsafe(32), "utf-8")
app.secret_key = secret_key.read_text("utf-8")


@app.template_filter("epoch_to_date")  # MARK: Filters
def epoch_to_date_filter(epoch):
    return datetime.fromtimestamp(epoch).strftime("%d.%m.%Y @ %H:%M ")


@app.teardown_appcontext  # MARK: DB teardown
def close_connection(_):  # Auto-closes the database connection
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@app.get("/public/<string:path>")  # Public dir route
def public(path):
    return send_from_directory("public", path)


@app.before_request  # MARK: Before request
def check_required_password_change():
    # If password change is required, only required routes are allowed
    if (
        "user" in session and
        session["user"]["require_new_password"] and
        not session["user"]["is_admin"] and
        request.path not in ["/reset-password", "/api/change-password"] and
        not request.path.startswith("/public/") and
        not request.path.startswith("/a/")
    ):
        return redirect("/reset-password")


@app.before_request
def check_csrf():  # Handle CSRF token for API endpoints
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
    elif "request_token" not in session:
        # Generate initial request token, if not present
        # Expired every logout
        session["request_token"] = token_urlsafe(16)


@app.get("/")  # MARK: Pages
@app.get("/c/<int:category_id>")
def home(category_id=None):
    page = int(request.args.get("page")
               if "page" in request.args.keys() else "0")
    categories = get_db().get_categories()

    # Make sure category is valid
    if isinstance(category_id, int) and category_id not in range(1, len(categories) + 1):
        return redirect("/")

    challenges = get_db().get_challenges(
        session["user"]["id"] if "user" in session else -1,
        category_id,
        page)
    return render_template("./pages/home.html",
                           at_home=request.path == "/",
                           challenges=challenges,
                           category_name=categories[category_id -
                                                    1].name if category_id else None,
                           page=page)


@app.get("/search")
def search():
    search_string = request.args.get("s")
    search_tab = ("users" if request.args.get("t") == "1" else "challenges")
    page = int(request.args.get("page")
               if "page" in request.args.keys() else "0")
    if not search_string:
        return "No search to perform.", 400

    users, challenges = [], []
    if search_tab == "users":
        users = get_db().search_users(search_string, page)
    else:
        challenges = get_db().search_challenges(search_string,
                                                session["user"]["id"] if "user" in session else -1,
                                                None,
                                                page)
    return render_template("./pages/search-results.html",
                           challenges=challenges,
                           users=users,
                           search_string=search_string,
                           page=page,
                           tab=search_tab)


@app.get("/login")
def login():
    # If already logged in, go to home page
    if "user" in session:
        return redirect("/")

    return render_template("./pages/login.html")


@app.get("/register")
def register():
    # If already logged in, go to home page
    if "user" in session:
        return redirect("/")

    return render_template("./pages/register.html")


@app.get("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.get("/reset-password")
def reset_password():
    return render_template("./pages/reset-password.html")


@app.get("/challenge-new")
def new_post():
    return render_template("./forms/challenge-new.html")


@app.get("/chall/<challenge_id>",
         defaults={"sub_path": "", "sub_action": "", "reply_id": ""})
@app.get("/chall/<challenge_id>/",
         defaults={"sub_path": "", "sub_action": "", "reply_id": ""})
@app.get("/chall/<int:challenge_id>/<path:sub_path>/",
         defaults={"sub_action": "", "reply_id": ""})
@app.get("/chall/<int:challenge_id>/<path:sub_path>/<int:reply_id>/<path:sub_action>")
def challenge(challenge_id, sub_path, reply_id, sub_action):
    # Performing actions requires to be logged in
    if sub_path and "user" not in session:
        return redirect("/login")

    user_id = session["user"]["id"] if "user" in session else -1
    page = int(request.args.get("page")
               if "page" in request.args.keys() else "0")
    try:
        challenge_data = get_db().get_challenge(user_id, challenge_id)
    except ChallengeNotFoundException:
        return redirect("/")

    # Get comments and submissions or comment/submission to edit
    comments_and_submissions, reply_to_edit = ([], None)
    if not reply_id:
        comments_and_submissions = get_db().get_challenge_replies(
            user_id, challenge_id, page)
    elif sub_path == "com":
        reply_to_edit = get_db().get_comment(user_id, reply_id)
    elif sub_path == "sub":
        reply_to_edit = get_db().get_submission(user_id, reply_id)
    else:
        return "Unknown reply type.", 404

    # Performing actions requires user to be admin or own the content
    # NOTE: Checked in API too
    if not session["user"]["is_admin"]:
        if sub_path in ("edit", "delete") and not sub_action and challenge_data.author_id != user_id:
            return redirect(f"/chall/{challenge_id}")
        if sub_action and reply_to_edit.author_id != user_id:
            return redirect(f"/chall/{challenge_id}/{reply_id}")

    # To send submissions, challenge must be accepting them
    # NOTE: Checked in API too
    if sub_path == "sub" and not sub_action and not challenge_data.accepts_submissions:
        return redirect(f"/chall/{challenge_id}")

    # Default challenge template
    template = "./pages/challenge.html"

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
                           challenge=challenge_data,
                           replies=comments_and_submissions,
                           reply_to_edit=reply_to_edit,
                           page=page)


@app.get("/me", defaults={"username": ""})
@app.get("/u/<string:username>")
def profile(username):
    # If accessing from /me, must be logged in
    if not username and "user" not in session:
        return redirect("/login")

    try:
        # Get user data
        user = get_db().get_user(
            username if username else session["user"]["username"])
    except UserNotFoundException:
        return redirect("/")

    page = int(request.args.get("page")
               if "page" in request.args.keys() else "0")
    content = get_db().get_user_content(session["user"]["id"] if "user" in session else -1,
                                        user.id, page)
    received_votes = get_db().get_received_votes(user.id)
    given_votes = get_db().get_given_votes(user.id)

    return render_template("./pages/profile.html",
                           profile=user.profile.to_dict(),
                           username=user.username,
                           content=content,
                           received_votes=received_votes,
                           given_votes=given_votes,
                           page=page)


@app.get("/me/edit", defaults={"username": ""})
@app.get("/u/<string:username>/edit")
def profile_edit(username):
    # If accessing from /me, must be logged in
    if not username and "user" not in session:
        return redirect("/login")

    # If using specified username, must be admin
    # NOTE: Checked in the API too.
    if username and not session["user"]["is_admin"]:
        return redirect("/me/edit")

    try:
        target_user = get_db().get_user(
            username if username else session["user"]["username"])
    except UserNotFoundException:
        return "User not found", 404

    return render_template("./forms/profile-edit.html",
                           profile=target_user.profile.to_dict(),
                           username=target_user.username)


@app.get("/me/settings", defaults={"username": ""})
@app.get("/u/<string:username>/settings")
def target_user_settings(username):
    # Must be logged in
    if "user" not in session:
        return redirect("/login")

    # Must be admin
    # NOTE: Checked in the API too
    if username and not session["user"]["is_admin"]:
        return redirect("/me/settings")

    # Get user
    user = get_db().get_user(
        username if username else session["user"]["username"])

    return render_template("./pages/user-settings.html", user=user)


@app.get("/a/<int:asset_id>")
def asset(asset_id):
    try:
        asset_to_send = get_db().get_asset(asset_id)
    except AssetNotFoundException:
        return redirect("/")

    response = Response(asset_to_send.value)
    response.headers["Content-Type"] = filename_to_file_type(
        asset_to_send.filename)
    return response


# MARK: API
app.add_url_rule("/api/login",
                 view_func=api_login, methods=["POST"])
app.add_url_rule("/api/register",
                 view_func=api_register, methods=["POST"])
app.add_url_rule("/api/profile/edit",
                 view_func=api_profile_edit, methods=["POST"])
app.add_url_rule("/api/post/challenge",
                 view_func=api_post_challenge, methods=["POST"])
app.add_url_rule("/api/edit/challenge",
                 view_func=api_edit_challenge, methods=["POST"])
app.add_url_rule("/api/delete/challenge",
                 view_func=api_delete_challenge, methods=["POST"])
app.add_url_rule("/api/vote/<string:target_type>/<int:target_id>",
                 view_func=api_vote, methods=["POST"])
app.add_url_rule("/api/post/comment",
                 view_func=api_post_comment, methods=["POST"])
app.add_url_rule("/api/edit/comment",
                 view_func=api_edit_comment, methods=["POST"])
app.add_url_rule("/api/delete/comment",
                 view_func=api_delete_comment, methods=["POST"])
app.add_url_rule("/api/post/submission",
                 view_func=api_post_submission, methods=["POST"])
app.add_url_rule("/api/edit/submission",
                 view_func=api_edit_submission, methods=["POST"])
app.add_url_rule("/api/delete/submission",
                 view_func=api_delete_submission, methods=["POST"])
app.add_url_rule("/api/change-password",
                 view_func=api_change_password, methods=["POST"])
app.add_url_rule("/api/admin/request-password-change",
                 view_func=api_require_password_change, methods=["POST"])


@app.errorhandler(NotFound)  # MARK: Default error handlers
def handle_exception_not_found(_):
    return "Not found.", 404


@app.errorhandler(Exception)
def handle_exception_general(e):
    print("Internal Server Error")
    print_exception(e)
    return "Internal server error.", 500
