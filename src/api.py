from re import S
from traceback import print_exception
from database.types import ChallengeNotFoundException, CommentNotFoundException, SubmissionNotFoundException, UserExistsException
from flask import redirect, request, session
from database.abstract import ProfileEditable, UserNotFoundException
from util.includes import includes
from util.password import is_good_password
from werkzeug.security import check_password_hash, generate_password_hash
from util.has_permission import has_permission
from util.get_db import get_db

# MARK: Login & Register
def api_login():
    if not includes(request.form, ["username", "password"]):
        return "Username or password missing.", 400

    username = request.form["username"]
    password = request.form["password"]

    # Attempt to get user
    try:
        user = get_db().get_user(username)
    except UserNotFoundException:
        return redirect("/login?fail")
    except Exception as err:
        print("Login Error:", err)
        return "Internal Server Error.", 500

    # Check password
    if check_password_hash(user.password_hash, password):
        session["user"] = user.to_dict()
        return redirect("/")
    else:
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
    
    except Exception as err:
        print("Register Error")
        print_exception(err)
        return "Internal Server Error.", 500
    
# MARK: User settings
def api_change_password():
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
        else:   
            session.clear()
            return redirect("/login")
        
    except UserNotFoundException:
        return "User does not exist.", 400
    except Exception as err:
        print("Password Change Error")
        print_exception(err)
        return "Internal Server Error.", 500
    
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
    
    except Exception as err:
        print("Password Change Request Error")
        print_exception(err)
        return "Internal Server Error.", 500

# MARK: Profiles
def api_profile_edit():
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

        # Delete existing assets, if necessary
        if user.profile.banner_asset and banner_file:
            get_db().remove_asset(user.profile.banner_asset.id)
        if user.profile.image_asset and image_file:
            get_db().remove_asset(user.profile.image_asset.id)

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

        # Refresh session
        session["user"] = get_db().get_user(username).to_dict() 
        return redirect("/me")
    except Exception as err:
        print("Profile Edit Error")
        print_exception(err)
        return "Internal Server Error.", 500

# MARK: Post Challenge
def api_post_challenge():
    if "user" not in session:
        return "Not logged in.", 401
    
    if not includes(request.form, ["title", "category", "body", "accepts_submissions"]):
        return "Incomplete data.", 400

    user_id = session["user"]["id"]
    title = request.form["title"]
    body = request.form["body"]
    attachments = request.files.getlist("attachments")
    try:
        category_id = int(request.form["category"])
        accepts_submissions = int(request.form["accepts_submissions"]) == 1
    except:
        return "Invalid data.", 400

    try:
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
        
    except Exception as err:
        print("Challenge Post Error")
        print_exception(err)
        return "Internal Server Error.", 500

# MARK: Edit Challenge
def api_edit_challenge():
    if "user" not in session:
        return "Not logged in.", 401
    
    if not includes(request.form, ["title", "category", "id", "accepts_submissions"]):
        return "Incomplete data.", 400

    title = request.form["title"]
    body = request.form["body"]
    challenge_id = request.form["id"]
    try:
        accepts_submissions = int(request.form["accepts_submissions"]) == 1
        category_id = int(request.form["category"])
    except:
        return "Invalid data.", 400

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
        
    except Exception as err:
        print("Challenge Edit Error")
        print_exception(err)
        return "Internal Server Error.", 500
    
# MARK: Delete Challenge
def api_delete_challenge():
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
        return redirect(f"/")
    
    except ChallengeNotFoundException:
        return "Challenge does not exit.", 400
        
    except Exception as err:
        print("Challenge Delete Error:")
        print_exception(err)
        return "Internal Server Error.", 500

# MARK: Vote
def api_vote(type, target_id):
    if "user" not in session:
        return "Not logged in.", 401
    
    if "vote_action" not in request.form.keys() or "from_page" not in request.form.keys():
        return "Incomplete data.", 400

    user_id = session["user"]["id"]
    vote_action  = request.form["vote_action"]
    from_page = request.form["from_page"]
    
    try:
        # Vote for or remove
        # FIXME: Does not check target exists, so we might create "ghost" votes.
        #       I don't see why that is an issue though.
        if vote_action == "1":
            get_db().vote_for(type, target_id, user_id)
        else:
            get_db().remove_vote_from(type, target_id, user_id)
        
        # Redirect back
        # Needs separate rules for each place the request can be from to properly focus/go to the right place back
        if from_page.startswith("/chall/"):
            if type == "comment":
                return redirect(from_page + "#com-" + target_id)
            
            return redirect("/chall/" + target_id)
        elif from_page == "/":
            return redirect("/#chall-" + target_id)
        else:
            return redirect(from_page + "#chall-" + target_id)
        
    except Exception as err:
        print("Vote Error")
        print_exception(err)
        return "Internal Server Error.", 500 

# MARK: Comment
def api_post_comment():
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
        
    except Exception as err:
        print("Comment Post Error")
        print_exception(err)
        return "Internal Server Error.", 500

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
        
    except Exception as err:
        print("Comment Edit Error")
        print_exception(err)
        return "Internal Server Error.", 500
    
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
        
    except Exception as err:
        print("Comment Delete Error")
        print_exception(err)
        return "Internal Server Error.", 500
    
# MARK: Submissions
def api_post_submission():
    if "user" not in session:
        return "Not logged in.", 401
    
    if not includes(request.form, ["title", "body", "challenge_id"]) or "script" not in request.files.keys():
        return "Incomplete data.", 400

    user_id = session["user"]["id"]
    challenge_id = request.form["challenge_id"]
    title = request.form["title"]
    body = request.form["body"]
    script = request.files["script"]
    script_name = script.filename + ".js" if not script.filename.endswith(".js") else script.filename

    try:
        # Verify challenge accepts submissions
        if not get_db().get_challenge(user_id, challenge_id).accepts_submissions:
            return "Challenge does not accept submissions.", 401
            
        # Create asset for submission
        script_asset = get_db().create_asset(script_name,
                                                    script.stream.read())
        
        # Create submission
        submission_id = get_db().create_submission(challenge_id, title, body, user_id, script_asset.id if script_asset else None)
 
        return redirect(f"/chall/{challenge_id}/#s-{submission_id}")
    
    except ChallengeNotFoundException:
        return "Challenge does not exit.", 400
        
    except Exception as err:
        print("Comment Post Error")
        print_exception(err)
        return "Internal Server Error.", 500
    
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
    if "script" in request.form.keys():
        script = request.files["script"]
        script_name = script.filename + ".js" if not script.filename.endswith(".js") else script.filename

    try:
        # Check permission
        submission = get_db().get_submission(session["user"]["id"], submission_id)
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

        return redirect(f"/chall/{submission.challenge_id}/#sub-{submission.id}")
    
    except SubmissionNotFoundException:
        return "Submission does not exit.", 400
        
    except Exception as err:
        print("Submission Edit Error")
        print_exception(err)
        return "Internal Server Error.", 500

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
        
    except Exception as err:
        print("Submission Delete Error")
        print_exception(err)
        return "Internal Server Error.", 500
