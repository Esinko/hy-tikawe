from flask import redirect, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from database.types import (
    ChallengeNotFoundException,
    CommentNotFoundException,
    SubmissionNotFoundException,
    UserExistsException
)
from database.abstract import ProfileEditable, UserNotFoundException
from util.includes import includes
from util.password import is_good_password
from util.get_db import get_db
from util.has_permission import has_permission


def api_login():  # MARK: Login & Register
    if not includes(request.form, ["username", "password"]):
        return "Username or password missing.", 400

    username = request.form["username"]
    password = request.form["password"]

    # Attempt to get user
    try:
        user = get_db().get_user(username)
    except UserNotFoundException:
        return redirect("/login?fail")

    # Check password
    if check_password_hash(user.password_hash, password):
        session["user"] = user.to_dict()
        return redirect("/")

    return redirect("/login?fail")


def api_register():
    if not includes(request.form, ["username", "password", "password-again"]):
        return "Username or password missing.", 400

    username = request.form["username"]
    password = request.form["password"]
    password_again = request.form["password-again"]

    # Check passwords match
    if password != password_again:
        return redirect("/register?mismatch")

    # Check password strength
    if not is_good_password(password):
        return redirect("/register?weak")

    try:
        # Create user
        user = get_db().create_user(username, generate_password_hash(password))
        session["user"] = user.to_dict()
        return redirect("/")

    except UserExistsException:
        return redirect("/register?taken")


def api_change_password():  # MARK: User settings
    if "user" not in session:
        return "Not logged in.", 401

    if not includes(request.form, ["password", "password-again"]):
        return "Incomplete data.", 400

    # If user is specified, session user must be admin
    if "u" in request.args and not session["user"]["is_admin"]:
        return "Permission denied.", 401

    username = request.args.get("u", session["user"]["username"])
    password = request.form["password"]
    password_again = request.form["password-again"]

    # Check passwords match
    if password != password_again:
        return redirect("/me/settings?p-mismatch")

    # Check password strength
    if not is_good_password(password):
        return redirect("/me/settings?p-weak")

    try:
        # Change password
        get_db().edit_user(username, {
            "username": username,
            "password_hash": generate_password_hash(password),
            "require_new_password": False
        })

        # Admin does not get logged out
        if "u" in request.args:
            return redirect(f"/u/{username}")

        session.clear()
        return redirect("/login")

    except UserNotFoundException:
        return "User does not exist.", 400


def api_require_password_change():
    if "user" not in session:
        return "Not logged in.", 401

    # Must be admin to use this endpoint
    if not session["user"]["is_admin"]:
        return "Permission denied.", 401

    if not includes(request.form, ["u"]):
        return "Incomplete data.", 400

    username = request.form["u"]
    required = "required" in request.form.keys()
    print("REQ", required)

    try:
        get_db().set_user_new_password_required(username, required)
        return redirect(f"/u/{username}/settings")

    except UserNotFoundException:
        return "User does not exist.", 400


def api_profile_edit():  # MARK: Profiles
    if "user" not in session:
        return "Not logged in.", 401

    if not includes(request.files, ["image", "banner"]) or "description" not in request.form.keys():
        return "Incomplete data.", 400

    username = session["user"]["username"]
    user_id = session["user"]["id"]
    description = request.form["description"]
    image_file = request.files["image"]
    banner_file = request.files["banner"]

    try:
        # Get user
        user = get_db().get_user(username)

        # Create new assets, if necessary
        image_file_id = user.profile.image_asset.id if user.profile.image_asset else None
        banner_file_id = user.profile.banner_asset.id if user.profile.banner_asset else None
        if image_file:
            new_image = get_db().create_asset(image_file.filename,
                                              image_file.stream.read())
            image_file_id = new_image.id
        if banner_file:
            new_banner = get_db().create_asset(banner_file.filename,
                                               banner_file.stream.read())
            banner_file_id = new_banner.id

        # Perform edits
        new_profile: ProfileEditable = {
            "image_asset_id": image_file_id,
            "banner_asset_id": banner_file_id,
            "description": description
        }
        get_db().edit_profile(user_id, new_profile)

        # Delete old assets, if necessary
        # Must be after edit_profile to ensure asset is no longer referenced
        if user.profile.banner_asset and banner_file:
            get_db().remove_asset(user.profile.banner_asset.id)
        if user.profile.image_asset and image_file:
            get_db().remove_asset(user.profile.image_asset.id)

        # Refresh session
        session["user"] = get_db().get_user(username).to_dict()
        return redirect("/me")

    except UserNotFoundException:
        return "User does not exist.", 400


def api_post_challenge():  # MARK: Post Challenge
    if "user" not in session:
        return "Not logged in.", 401

    if not includes(request.form, ["title", "category", "body", "accepts_submissions"]):
        return "Incomplete data.", 400

    user_id = session["user"]["id"]
    title = request.form["title"]
    body = request.form["body"]
    try:
        category_id = int(request.form["category"])
        accepts_submissions = int(request.form["accepts_submissions"]) == 1
    except ValueError:
        return "Invalid data.", 400

    # Check challenge category is valid
    categories = get_db().get_categories()
    if not any(category.id == category_id for category in categories):
        return "Invalid category.", 400

    # Create challenge post
    post_id = get_db().create_challenge(title,
                                        body,
                                        category_id,
                                        user_id,
                                        accepts_submissions)
    return redirect(f"/chall/{post_id}")


def api_edit_challenge():  # MARK: Edit Challenge
    if "user" not in session:
        return "Not logged in.", 401

    if not includes(request.form, ["title", "category", "id", "accepts_submissions"]):
        return "Incomplete data.", 400

    title = request.form["title"]
    body = request.form["body"]
    challenge_id = request.form["id"]
    accepts_submissions = int(request.form["accepts_submissions"]) == 1
    category_id = int(request.form["category"])

    try:
        # Check challenge category is valid
        categories = get_db().get_categories()
        if not any(category.id == category_id for category in categories):
            return "Invalid category.", 400

        # Check permission
        challenge = get_db().get_challenge(session["user"]["id"], challenge_id)
        if not has_permission(session["user"], "edit", "challenge", challenge.author_id):
            return "Permission denied.", 401

        # Edit challenge post
        # TODO: Add edited date?
        get_db().edit_challenge(challenge_id, {
            "body": body,
            "category_id": category_id,
            "title": title,
            "accepts_submissions": accepts_submissions
        })
        return redirect(f"/chall/{challenge_id}")

    except ChallengeNotFoundException:
        return "Challenge does not exit.", 400


def api_delete_challenge():  # MARK: Delete Challenge
    if "user" not in session:
        return "Not logged in.", 401

    if "id" not in request.form.keys():
        return "Incomplete data.", 400

    challenge_id = request.form["id"]

    try:
        challenge = get_db().get_challenge(session["user"]["id"], challenge_id)

        # Check permission
        if not has_permission(session["user"], "delete", "challenge", challenge.author_id):
            return "Permission denied.", 401

        # Delete challenge
        get_db().remove_challenge(challenge_id)
        return redirect("/")

    except ChallengeNotFoundException:
        return "Challenge does not exit.", 400


def api_vote(target_type, target_id):  # MARK: Vote
    if "user" not in session:
        return "Not logged in.", 401

    if "vote_action" not in request.form.keys() or "from_page" not in request.form.keys():
        return "Incomplete data.", 400

    user_id = session["user"]["id"]
    vote_action = request.form["vote_action"]
    from_page = request.form["from_page"]

    # FIXME: Does not check target exists, so we might create "ghost" votes.
    #       I don't see why that is an issue though.
    if vote_action == "1":
        get_db().vote_for(target_type, target_id, user_id)
    else:
        get_db().remove_vote_from(target_type, target_id, user_id)

    # Redirect back
    # Needs separate rules for each place the request can be from.
    # To properly focus/go to the right place back
    tag = {
        "comment": "com",
        "submission": "sub",
        "challenge": "chall"
    }
    target_tag = tag.get(target_type, "chall")

    return redirect(from_page + f"#{target_tag}-" + str(target_id))


def api_post_comment():  # MARK: Comment
    if "user" not in session:
        return "Not logged in.", 401

    if "body" not in request.form.keys() or "challenge_id" not in request.form.keys():
        return "Incomplete data.", 400

    user_id = session["user"]["id"]
    challenge_id = request.form["challenge_id"]
    body = request.form["body"]

    try:
        # Create challenge comment
        comment_id = get_db().create_comment(challenge_id, body, user_id)
        return redirect(f"/chall/{challenge_id}/#c-{comment_id}")

    except ChallengeNotFoundException:
        return "Challenge does not exit.", 400


def api_edit_comment():
    if "user" not in session:
        return "Not logged in.", 401

    if "body" not in request.form.keys() or "id" not in request.form.keys():
        return "Incomplete data.", 400

    body = request.form["body"]
    comment_id = request.form["id"]

    try:
        # Check permission
        comment = get_db().get_comment(session["user"]["id"], comment_id)
        if not has_permission(session["user"], "edit", "comment", comment.author_id):
            return "Permission denied.", 401

        # TODO: Add edited date?
        get_db().edit_comment(comment_id, {
            "body": body
        })
        return redirect(f"/chall/{comment.challenge_id}/#com-{comment_id}")

    except CommentNotFoundException:
        return "Comment does not exist.", 400


def api_delete_comment():
    if "user" not in session:
        return "Not logged in.", 401

    if "id" not in request.form.keys():
        return "Incomplete data.", 400

    comment_id = request.form["id"]

    try:
        comment = get_db().get_comment(session["user"]["id"], comment_id)

        # Check permission
        if not has_permission(session["user"], "delete", "challenge", comment.author_id):
            return "Permission denied.", 401

        # Delete challenge
        get_db().remove_comment(comment.id)
        return redirect(f"/chall/{comment.challenge_id}")

    except CommentNotFoundException:
        return "Challenge does not exit.", 400


def api_post_submission():  # MARK: Submissions
    if "user" not in session:
        return "Not logged in.", 401

    if (
        not includes(request.form, ["title", "body", "challenge_id"]) or
        "script" not in request.files.keys()
    ):
        return "Incomplete data.", 400

    user_id = session["user"]["id"]
    challenge_id = request.form["challenge_id"]
    title = request.form["title"]
    body = request.form["body"]
    script = request.files["script"]
    script_name = script.filename + \
        ".js" if not script.filename.endswith(".js") else script.filename

    try:
        # Verify challenge accepts submissions
        if not get_db().get_challenge(user_id, challenge_id).accepts_submissions:
            return "Challenge does not accept submissions.", 401

        # Create asset for submission
        script_asset = get_db().create_asset(script_name,
                                             script.stream.read())

        # Create submission
        submission_id = get_db().create_submission(challenge_id,
                                                   title,
                                                   body,
                                                   user_id,
                                                   script_asset.id if script_asset else None)

        return redirect(f"/chall/{challenge_id}/#s-{submission_id}")

    except ChallengeNotFoundException:
        return "Challenge does not exit.", 400


def api_edit_submission():
    if "user" not in session:
        return "Not logged in.", 401

    if not includes(request.form, ["body", "id", "title"]):
        return "Incomplete data.", 400

    submission_id = request.form["id"]
    title = request.form["title"]
    body = request.form["body"]

    # Script replacement is optional, maintain original if not present
    script, script_name = None, None
    if "script" in request.files.keys():
        script = request.files["script"]
        script_name = script.filename + \
            ".js" if not script.filename.endswith(".js") else script.filename

    try:
        # Check permission
        submission = get_db().get_submission(
            session["user"]["id"], submission_id)
        if not has_permission(session["user"], "edit", "submission", submission.author_id):
            return "Permission denied.", 401

        # TODO: Add edited date?
        get_db().edit_submission(submission.id, {
            "title": title,
            "body": body,
            "script_id": submission.script_id if not script else None,
            "script_name": script_name,
            "script_bytes": script.stream.read() if script else None
        })

        # Delete original asset, if required
        if script:
            get_db().remove_asset(submission.script_id)

        return redirect(f"/chall/{submission.challenge_id}/#sub-{submission.id}")

    except SubmissionNotFoundException:
        return "Submission does not exit.", 400


def api_delete_submission():
    if "user" not in session:
        return "Not logged in.", 401

    if "id" not in request.form.keys():
        return "Incomplete data.", 400

    submission_id = request.form["id"]

    try:
        submission = get_db().get_comment(session["user"]["id"], submission_id)

        # Check permission
        if not has_permission(session["user"], "delete", "submission", submission.author_id):
            return "Permission denied.", 401

        # Delete challenge
        get_db().remove_submission(submission.id)
        return redirect(f"/chall/{submission.challenge_id}")

    except CommentNotFoundException:
        return "Challenge does not exit.", 400
