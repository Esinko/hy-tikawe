from typing import Literal
from database.types import UserDict


def has_permission(  # Logic for checking permissions for users
        user: UserDict,
        action: Literal["delete", "create", "edit", "view"],
        target_type: Literal["profile", "user", "challenge", "comment", "submission"],
        target_owner_id: int
):
    # Pre: if not user provided, deny
    if not user:
        return False

    # 1. If the user is admin, allow everything
    if user["is_admin"]:
        return True

    # 2. Creation of challenges, comments and submissions is allowed except:
    #    - When the require_new_password is set
    # NOTE: Locking challenges will lead to a check here
    if (
        action == "create" and
        target_type in ("challenge", "comment", "submission") and
        not user["require_new_password"]
    ):
        return True

    # 3. Editing and deleting allowed if the user owns the content
    if action in ("edit", "delete") and target_owner_id == user["id"]:
        return True

    # 4. Viewing is always allowed for profiles, challenges, comments and submissions
    # NOTE: Limiting/hiding things will lead to a check here
    # NOTE: Viewing of user is considered and admin only action
    if action == "view" and target_type in ("challenge", "comment", "profile", "submission"):
        return True

    return False
