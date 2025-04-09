# Database abstractions on top of SQL to make development easier
# Implements complex functions to perform tasks (not just "commands") against the database

from time import time
from typing import List, Literal
from database.sql import sql_table
from database.connection import DatabaseConnection
from database.types import (
    Asset,
    AssetNotFoundException,
    Category,
    ChallengeHusk,
    ChallengeEditable,
    ChallengeNotFoundException,
    Profile,
    ProfileEditable,
    ProfileNotFoundException,
    User,
    UserEditable,
    UserExistsException,
    UserNotFoundException,
    CommentEditable,
    CommentNotFoundException,
    CommentHusk,
    SubmissionHusk,
    StatsDict,
    StatsException
)

class AbstractDatabase:
    def __init__(self, connection=DatabaseConnection):
        self.connection = connection

    # MARK: User Abstractions
    def user_exists(self, username: str) -> bool:
        # Check if user exists
        return self.connection.query(query=sql_table["user_exists"], parameters=(username,), limit=1)[0][0] == 1

    def create_user(self, username: str, password_hash: str) -> User:
        # Check if user exists
        if self.user_exists(username):
            raise UserExistsException(username)
        
        # Create user
        _, cursor = self.connection.execute(query=sql_table["create_user"], parameters=(username, password_hash))
        user_id = cursor.lastrowid
        cursor.close()

        # Crete profile
        _, cursor = self.connection.execute(query=sql_table["create_profile"], parameters=(user_id,))
        cursor.close()
        return self.get_user(username)
    
    def get_user(self, username: str) -> User:
        # TODO: Use table joins to get all the user info at once?
        # Get user
        result = self.connection.query(query=sql_table["get_user"], parameters=(username,), limit=1)
        if len(result) == 0:
            raise UserNotFoundException(username)
        
        user_data = result[0]
        user_profile = self.get_profile(user_data[0])
        
        return User(user_data[0],
                    user_data[1],
                    user_data[2],
                    user_data[3] == 1,
                    user_data[4] == 1,
                    user_profile)
    
    def edit_user(self, username: str, new_fields: UserEditable):
        # Check if user exists
        if not self.user_exists(username):
            raise UserNotFoundException(username)
        
        _, cursor = self.connection.execute(query=sql_table["edit_user"], parameters=(new_fields["username"], new_fields["password_hash"], new_fields["require_new_password"], username))
        cursor.close()

    # MARK: Profile Abstractions
    def get_profile(self, user_id: int):
        # Get profile
        [profile_data] = self.connection.query(query=sql_table["get_profile"], parameters=(user_id,))
        if not profile_data:
            raise ProfileNotFoundException(user_id)
        
        # Get assets
        image_asset = self.get_asset(profile_data[2]) if profile_data[2] else None
        banner_asset = self.get_asset(profile_data[3]) if profile_data[3] else None
        
        return Profile(profile_data[0],
                       user_id,
                       profile_data[1],
                       image_asset,
                       banner_asset)

    def profile_exists(self, user_id: int):
        return self.connection.query(query=sql_table["profile_exists"], parameters=(user_id,), limit=1)[0][0] == 1

    def edit_profile(self, user_id: int, new_fields: ProfileEditable):
        if not self.profile_exists(user_id):
            raise ProfileNotFoundException(user_id)
        
        _, cursor = self.connection.execute(query=sql_table["edit_profile"], parameters=(new_fields["description"], new_fields["image_asset_id"], new_fields["banner_asset_id"], user_id))
        cursor.close()
        
    # MARK: Asset abstractions
    def create_asset(self, filename: str, value: bytes) -> Asset:
        _, cursor = self.connection.execute(query=sql_table["create_asset"], parameters=(filename, value))
        asset_id = cursor.lastrowid
        cursor.close()

        return Asset(asset_id, filename, value)
    
    def get_asset(self, asset_id: int) -> Asset:
        [asset] = self.connection.query(query=sql_table["get_asset"], parameters=(asset_id,), limit=1)
        if not asset:
            raise AssetNotFoundException(asset_id)
        return Asset(asset_id, asset[0], asset[1])
    
    def delete_asset(self, asset_id: int):
        self.connection.execute(query=sql_table["delete_asset"], parameters=(asset_id,))
    
    # MARK: Categ. abstractions
    def get_categories(self) -> List[Category]:
        results = self.connection.query(query=sql_table["get_categories"])
        categories = []
        for result in results:
            categories.append(Category(result[0], result[1]))

        return categories
    
    # MARK: Chall. abstractions
    def get_challenges(self, current_user_id: int, category_id: int | None, page: int) -> List[ChallengeHusk]:
        page_size = 10
        results = self.connection.query(query=sql_table["get_full_challenges"], parameters=(current_user_id, category_id, category_id, page_size, page * page_size))
        challenges = []
        for result in results:
            challenges.append(ChallengeHusk(*result))
        return challenges
    
    def get_challenge(self, current_user_id: int, challenge_id: int) -> ChallengeHusk:
        [result] = self.connection.query(query=sql_table["get_full_challenge"], parameters=(current_user_id, challenge_id))
        if not result:
            raise ChallengeNotFoundException(challenge_id)
        return ChallengeHusk(*result)
    
    def get_challenge_replies(self, current_user_id: int, challenge_id: int) -> List[CommentHusk | SubmissionHusk]:
        # TODO: Pagination
        results = self.connection.query(query=sql_table["get_comments_and_submissions"], parameters=(current_user_id, challenge_id, current_user_id, challenge_id), limit=100)
        
        all_replies = []
        for entry_type, *result in results:
            if entry_type == "comment":
                all_replies.append(CommentHusk(*result[0:-3]))
            else:
                all_replies.append(SubmissionHusk(*result))

        return all_replies
    
    def challenge_exists(self, challenge_id: int) -> bool:
        return self.connection.query(query=sql_table["challenge_exists"], parameters=(challenge_id,), limit=1)[0][0] == 1

    def edit_challenge(self, challenge_id: int, new_fields: ChallengeEditable):
        # Check if challenge exists
        if not self.challenge_exists(challenge_id):
            raise ChallengeNotFoundException(challenge_id)
        
        _, cursor = self.connection.execute(query=sql_table["edit_challenge"], parameters=(new_fields["title"], new_fields["body"], new_fields["category_id"], 1 if new_fields["accepts_submissions"] else 0, challenge_id))
        cursor.close()

    def remove_challenge(self, challenge_id: int):
        _, cursor = self.connection.execute(query=sql_table["remove_challenge"], parameters=(challenge_id,))
        cursor.close()

    def create_challenge(self, title: str, body: str, category_id: int, author_id: int, accepts_submissions: bool) -> int:
        _, cursor = self.connection.execute(query=sql_table["create_challenge"], parameters=(int(time()), title, body, category_id, author_id, 1 if accepts_submissions else 0))
        post_id = cursor.lastrowid
        cursor.close()
        return post_id
    
    def search_challenge(self, search_string: str, current_user_id: int, category_id: int | None, page: int):
        page_size = 10
        results = self.connection.query(query=sql_table["search_challenges"], parameters=(current_user_id, category_id, category_id, search_string, search_string, page_size, page * page_size))
        challenges = []
        for result in results:
            challenges.append(ChallengeHusk(*result))
        return challenges

    # MARK: Voting abstractions
    def vote_for(self, type: Literal["submission", "comment", "challenge"], target_id: int, user_id: int):
        statement = ""
        if type == "submission":
            statement = sql_table["create_vote_for_submission"]
        elif type == "challenge":
            statement = sql_table["create_vote_for_challenge"]
        elif type == "comment":
            statement  = sql_table["create_vote_for_comment"]
        else:
            raise Exception("Unknown target type!")

        _, cursor = self.connection.execute(query=statement, parameters=(target_id, user_id))
        cursor.close()

    def remove_vote_from(self, type: Literal["submission", "comment", "challenge"], target_id: int, user_id: int):
        statement = ""
        if type == "submission":
            statement = sql_table["remove_vote_from_submission"]
        elif type == "challenge":
            statement = sql_table["remove_vote_from_challenge"]
        elif type == "comment":
            statement  = sql_table["remove_vote_from_comment"]
        else:
            raise Exception("Unknown target type!")

        _, cursor = self.connection.execute(query=statement, parameters=(target_id, user_id))
        cursor.close()

    # MARK: Comment abstractions
    def create_comment(self, challenge_id: int, body: str, author_id: int) -> int:
        _, cursor = self.connection.execute(query=sql_table["create_comment"], parameters=(int(time()), challenge_id, body, author_id))
        comment_id = cursor.lastrowid
        cursor.close()
        return comment_id
    
    def remove_comment(self, comment_id: int):
        _, cursor = self.connection.execute(query=sql_table["remove_comment"], parameters=(comment_id,))
        cursor.close()

    def get_comment(self, current_user_id: int,comment_id: int) -> CommentHusk:
        [result] = self.connection.query(query=sql_table["get_comment"], parameters=(current_user_id, comment_id))
        if not result:
            raise CommentNotFoundException(comment_id)
        return CommentHusk(*result)

    def comment_exists(self, comment_id: int) -> bool:
        return self.connection.query(query=sql_table["comment_exists"], parameters=(comment_id,), limit=1)[0][0] == 1

    def edit_comment(self, comment_id: int, new_fields: CommentEditable):
        # Check if challenge exists
        if not self.comment_exists(comment_id):
            raise CommentNotFoundException(comment_id)
        
        _, cursor = self.connection.execute(query=sql_table["edit_comment"], parameters=(new_fields["body"], comment_id))
        cursor.close()

    # MARK: Submissions abstractions
    def create_submission(self, challenge_id: int, title: str, body: str, author_id: int) -> int:
        _, cursor = self.connection.execute(query=sql_table["create_submission"], parameters=(int(time()), challenge_id, title, body, None, author_id))
        submission_id = cursor.lastrowid
        cursor.close()
        return submission_id
    
    def remove_submission(self, submission_id: int):
        _, cursor = self.connection.execute(query=sql_table["remove_submission"], parameters=(submission_id,))
        cursor.close()

    # MARK: Get all user content

    def _transform_to_reply(self, result):
        return (
            result[1],      # id
            result[2],      # created
            result[4],      # body
            result[9],      # author_id
            result[8],      # username
            result[10],     # image_asset_id
            result[11],     # vote_count
            result[12],     # has_my_vote
            result[0],      # challenge_id (target_challenge_id)
            result[3],      # title
            None,           # solution_asset_id
            None            # solution_filename
        )

    def get_user_content(self, as_user_id: int, for_user_id: int) -> List[ChallengeHusk | CommentHusk | SubmissionHusk]:
        results = self.connection.query(query=sql_table["get_user_content"], parameters=(as_user_id, for_user_id, as_user_id, for_user_id, as_user_id, for_user_id))
        content = []
        for entry_type, *result in results:
            if entry_type == "challenge":
                content.append(ChallengeHusk(*result[1:]))
            elif entry_type == "comment":
                content.append(CommentHusk(*self._transform_to_reply(result)[:9]))
            else:
                content.append(SubmissionHusk(*self._transform_to_reply(result)))
        return content

    # MARK: Vote statistics

    def get_received_votes(self, user_id: int) -> StatsDict:
        [result] = self.connection.query(query=sql_table["get_received_votes"], parameters=(user_id, user_id, user_id))
        if not result:
            raise StatsException("Unexpected stats (recv) query error.")
        return {
            "challenge": result[0],
            "comment": result[1],
            "submission": result[2]
        }
    
    def get_given_votes(self, user_id: int) -> StatsDict:
        [result] = self.connection.query(query=sql_table["get_given_votes"], parameters=(user_id, user_id, user_id))
        if not result:
            raise StatsException("Unexpected stats (give) query error.")
        return {
            "challenge": result[0],
            "comment": result[1],
            "submission": result[2]
        }
    