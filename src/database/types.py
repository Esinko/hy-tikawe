# Typings for database abstractions and some related exceptions

from typing import Optional, TypedDict


class DatabaseException(Exception):
    def __init__(self, message):
        super().__init__(message)


class Asset:
    id: str
    filename: str
    value: bytes

    def __init__(self, asset_id, filename, value):
        self.id = asset_id
        self.filename = filename
        self.value = value

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename
        }


class AssetNotFoundException(Exception):
    def __init__(self, asset_id):
        super().__init__(f"Asset for id '{asset_id}' not found.")


class Profile:
    id: str
    user_id: str
    description: str
    image_asset: Optional[Asset]
    banner_asset: Optional[Asset]

    def __init__(self, profile_id, user_id, description, image_asset, banner_asset):
        self.id = profile_id
        self.user_id = user_id
        self.description = description
        self.image_asset = image_asset
        self.banner_asset = banner_asset

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "description": self.description,
            "image_asset": self.image_asset.to_dict() if self.image_asset else None,
            "banner_asset": self.banner_asset.to_dict() if self.banner_asset else None
        }


class ProfileEditable(TypedDict):
    description: str
    image_asset_id: Optional[int]
    banner_asset_id: Optional[int]


class UserDict(TypedDict):
    id: str
    username: str
    password_hash: str
    require_new_password: bool
    profile: Profile
    is_admin: bool


class User:
    id: str
    username: str
    password_hash: str
    require_new_password: bool
    profile: Profile
    is_admin: bool

    def __init__(self,
                 user_id,
                 username,
                 password_hash,
                 require_new_password,
                 is_admin,
                 profile):
        self.id = user_id
        self.username = username
        self.password_hash = password_hash
        self.require_new_password = require_new_password == 1
        self.is_admin = is_admin == 1
        self.profile = profile

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "password_hash": self.password_hash,
            "require_new_password": self.require_new_password,
            "is_admin": self.is_admin,
            "profile": self.profile.to_dict()
        }


class UserEditable(TypedDict):
    username: str
    password_hash: str
    require_new_password: bool


class UserExistsException(Exception):
    def __init__(self, username):
        super().__init__(f"User '{username}' already exists!")


class UserNotFoundException(Exception):
    def __init__(self, username):
        super().__init__(f"User '{username}' not found.")


class ProfileNotFoundException(Exception):
    def __init__(self, user_id):
        super().__init__(f"Profile for user_id '{user_id}' not found.")


class Category:
    id: int
    name: str

    def __init__(self, category_id, name):
        self.id = category_id
        self.name = name

# FIXME: The types for challenges, comments and submissions are incomplete,
#        when it comes to giving the developer as much information to work with,
#        in favor of performance. We could build full User, Profile, Asset etc.
#        classes with little effort, but I think the choice I made here is the right one.
#        However, it may not be final.
#        Classes effected by this are named "Husks"


class ChallengeHusk:
    id: int
    type = "challenge"
    created: int
    title: str
    body: str
    accepts_submissions: bool
    category_id: str
    category_name: str
    author_name: str
    author_id: int
    author_image_id: int
    votes: int
    has_my_vote: bool

    def __init__(self,
                 challenge_id,
                 created,
                 title,
                 body,
                 accepts_submissions,
                 category_id,
                 category_name,
                 author_name,
                 author_id,
                 author_image_id,
                 votes,
                 has_my_vote):
        self.id = challenge_id
        self.created = created
        self.title = title
        self.body = body
        self.accepts_submissions = accepts_submissions == 1
        self.category_id = category_id
        self.category_name = category_name
        self.author_name = author_name
        self.author_id = author_id
        self.author_image_id = author_image_id
        self.votes = votes
        self.has_my_vote = has_my_vote == 1

    def to_dict(self):
        return {
            "id": self.id,
            "created": self.created,
            "title": self.title,
            "body": self.body,
            "category_name": self.category_name,
            "author_name": self.author_name,
            "author_image_id": self.author_image_id,
            "votes": self.votes,
            "has_my_vote": self.has_my_vote
        }


class ChallengeEditable(TypedDict):
    title: str
    body: str
    category_id: int
    accepts_submissions: bool


class ChallengeNotFoundException(Exception):
    def __init__(self, challenge_id):
        super().__init__(f"Challenge '{challenge_id}' not found.")


class CommentNotFoundException(Exception):
    def __init__(self, comment_id):
        super().__init__(f"Comment '{comment_id}' not found.")


class CommentEditable(TypedDict):
    body: str


class CommentHusk:
    id: int
    type = "comment"
    created: int
    body: str
    author_id: int
    author_image_id: int
    author_name: str
    challenge_id: int
    votes: int
    has_my_vote: bool

    def __init__(self,
                 comment_id,
                 created,
                 body,
                 author_id,
                 author_name,
                 author_image_id,
                 votes,
                 has_my_vote,
                 challenge_id):
        self.id = comment_id
        self.created = created
        self.body = body
        self.author_id = author_id
        self.author_name = author_name
        self.author_image_id = author_image_id
        self.votes = votes
        self.has_my_vote = has_my_vote == 1
        self.challenge_id = challenge_id


class SubmissionHusk:
    id: int
    type = "submission"
    created: int
    title: str
    body: str
    author_id: int
    author_image_id: int
    author_name: str
    challenge_id: int
    votes: int
    has_my_vote: bool
    script_id: int
    script_name: str

    def __init__(self,
                 submission_id,
                 created,
                 body,
                 author_id,
                 author_name,
                 author_image_id,
                 votes,
                 has_my_vote,
                 challenge_id,
                 title,
                 asset_id,
                 asset_name):
        self.id = submission_id
        self.created = created
        self.body = body
        self.author_id = author_id
        self.author_name = author_name
        self.author_image_id = author_image_id
        self.votes = votes
        self.has_my_vote = has_my_vote == 1
        self.challenge_id = challenge_id
        self.title = title
        self.script_name = asset_name
        self.script_id = asset_id


class SubmissionNotFoundException(Exception):
    def __init__(self, submission_id):
        super().__init__(f"Submission '{submission_id}' not found.")


class SubmissionEditable(TypedDict):
    title: str
    body: str
    script_id: Optional[int]
    script_name: str
    script_bytes: str


class StatsDict(TypedDict):
    challenge: int
    comment: int
    submission: int


class StatsException(Exception):
    def __init__(self, message):
        super().__init__(message)
