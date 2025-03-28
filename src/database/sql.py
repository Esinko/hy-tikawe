# All SQL commands used by the database library
sql_table = {
    "user_exists": "SELECT EXISTS (SELECT username FROM Users WHERE username = ?)",

    "create_user": "INSERT INTO Users (username, password_hash, require_new_password) VALUES (?, ?, False)",

    "get_user": "SELECT id, username, password_hash, require_new_password, is_admin FROM Users WHERE username = ?",

    "edit_user": "UPDATE Users SET name = ?, password_hash = ?, require_new_password = ? WHERE name = ?",

    "create_profile": "INSERT INTO Profiles (user_id, description, image_asset_id, banner_asset_id) VALUES (?, '', NULL, NULL)",

    "get_profile": "SELECT id, description, image_asset_id, banner_asset_id FROM Profiles WHERE user_id = ?",

    "profile_exists": "SELECT EXISTS (SELECT user_id FROM Profiles WHERE user_id = ?)",

    "edit_profile": "UPDATE Profiles SET description = ?, image_asset_id = ?, banner_asset_id = ? WHERE user_id = ?",

    "create_asset": "INSERT INTO Assets (filename, value) VALUES (?, ?)",

    "get_asset": "SELECT filename, value FROM Assets WHERE id = ?",

    "delete_asset": "DELETE FROM Assets WHERE id = ?",

    "get_categories": "SELECT id, name FROM ChallengeCategories",

    "get_full_challenges": """
        SELECT 
            C.id, 
            C.created, 
            C.title, 
            C.body,
            C.accepts_submissions,
            ChallengeCategories.id AS category_id, 
            ChallengeCategories.name AS category_name, 
            Users.username,
            Users.id,
            Profiles.image_asset_id AS profile_image,
            COALESCE(VoteCounts.vote_count, 0) AS vote_count,
            CASE WHEN UserVotes.voter_id IS NOT NULL THEN 1 ELSE 0 END AS has_voted
        FROM Challenges C
        JOIN ChallengeCategories ON C.category_id = ChallengeCategories.id
        JOIN Users ON C.author_id = Users.id
        JOIN Profiles ON Profiles.user_id = Users.id
        LEFT JOIN (
            SELECT challenge_id, COUNT(*) AS vote_count
            FROM Votes
            WHERE challenge_id IS NOT NULL
            GROUP BY challenge_id
        ) AS VoteCounts ON VoteCounts.challenge_id = C.id
        LEFT JOIN (
            SELECT challenge_id, voter_id
            FROM Votes
            WHERE voter_id = ?
        ) AS UserVotes ON UserVotes.challenge_id = C.id
        WHERE (? IS NULL OR C.category_id = ?)
        ORDER BY C.created DESC
        LIMIT ? OFFSET ?;
    """,

    "get_full_challenge": """
        SELECT 
            C.id, 
            C.created, 
            C.title, 
            C.body,
            C.accepts_submissions,
            ChallengeCategories.id AS category_id, 
            ChallengeCategories.name AS category_name, 
            Users.username,
            Users.id,
            Profiles.image_asset_id AS profile_image,
            COALESCE(VoteCounts.vote_count, 0) AS vote_count,
            CASE WHEN UserVotes.voter_id IS NOT NULL THEN 1 ELSE 0 END AS has_voted
        FROM Challenges C
        JOIN ChallengeCategories ON C.category_id = ChallengeCategories.id
        JOIN Users ON C.author_id = Users.id
        JOIN Profiles ON Profiles.user_id = Users.id
        LEFT JOIN (
            SELECT challenge_id, COUNT(*) AS vote_count
            FROM Votes
            WHERE challenge_id IS NOT NULL
            GROUP BY challenge_id
        ) AS VoteCounts ON VoteCounts.challenge_id = C.id
        LEFT JOIN (
            SELECT challenge_id, voter_id
            FROM Votes
            WHERE voter_id = ?
        ) AS UserVotes ON UserVotes.challenge_id = C.id
        WHERE C.id = ?
        LIMIT 1
    """,

    "create_challenge": "INSERT INTO Challenges (created, title, body, category_id, author_id, accepts_submissions) VALUES (?, ?, ?, ?, ?, ?)",

    "challenge_exists": "SELECT EXISTS (SELECT id FROM Challenges WHERE id = ?)",

    "edit_challenge": "UPDATE Challenges SET title = ?, body = ?, category_id = ?, accepts_submissions = ? WHERE id = ?",

    "remove_challenge": "DELETE FROM Challenges WHERE id = ?",

    "search_challenges": """
        SELECT 
            C.id, 
            C.created, 
            C.title, 
            C.body,
            C.accepts_submissions,
            ChallengeCategories.id AS category_id, 
            ChallengeCategories.name AS category_name, 
            Users.username, 
            Profiles.image_asset_id AS profile_image,
            COALESCE(VoteCounts.vote_count, 0) AS vote_count,
            CASE WHEN UserVotes.voter_id IS NOT NULL THEN 1 ELSE 0 END AS has_voted
        FROM Challenges C
        JOIN ChallengeCategories ON C.category_id = ChallengeCategories.id
        JOIN Users ON C.author_id = Users.id
        JOIN Profiles ON Profiles.user_id = Users.id
        LEFT JOIN (
            SELECT challenge_id, COUNT(*) AS vote_count
            FROM Votes
            WHERE challenge_id IS NOT NULL
            GROUP BY challenge_id
        ) AS VoteCounts ON VoteCounts.challenge_id = C.id
        LEFT JOIN (
            SELECT challenge_id, voter_id
            FROM Votes
            WHERE voter_id = ?
        ) AS UserVotes ON UserVotes.challenge_id = C.id
        WHERE 
            (? IS NULL OR C.category_id = ?)
            AND (
                LOWER(C.title) LIKE LOWER('%' || ? || '%') OR
                LOWER(C.body) LIKE LOWER('%' || ? || '%')
            )
        ORDER BY C.created DESC
        LIMIT ? OFFSET ?;
    """,

    "create_vote_for_challenge": "INSERT INTO Votes (challenge_id, voter_id) VALUES (?, ?)",
    
    "create_vote_for_comment": "INSERT INTO Votes (comment_id, voter_id) VALUES (?, ?)" ,

    "create_vote_for_submission": "INSERT INTO Votes (submission_id, voter_id) VALUES (?, ?)",

    "remove_vote_from_challenge": "DELETE FROM Votes WHERE challenge_id = ? AND voter_id = ?",

    "remove_vote_from_comment": "DELETE FROM Votes WHERE comment_id = ? AND voter_id = ?" ,

    "remove_vote_from_submission": "DELETE FROM Votes WHERE submission_id = ? AND voter_id = ?",

    "create_comment": "INSERT INTO Comments (created, challenge_id, body, author_id) VALUES (?, ?, ?, ?)",

    "get_comments": """ 
        SELECT
            Comments.id,
            Comments.created,
            Comments.body,
            Users.username,
            Profiles.image_asset_id
        FROM Comments
        JOIN Users ON Comments.author_id = Users.id
        LEFT JOIN Profiles ON Users.id = Profiles.user_id
        WHERE Comments.challenge_id = ?
        ORDER BY Comments.created ASC
    """ 
}

