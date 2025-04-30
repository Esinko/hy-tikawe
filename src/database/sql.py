# All SQL commands used by the database library
sql_table = {
    # MARK: User

    "user_exists": "SELECT EXISTS (SELECT username FROM Users WHERE username = ?)",

    "create_user": "INSERT INTO Users (username, password_hash, require_new_password) VALUES (?, ?, False)",

    "get_user": """
        SELECT
            id,
            username,
            password_hash,
            require_new_password,
            is_admin 
        FROM Users WHERE username = ?
    """,

    "edit_user": "UPDATE Users SET name = ?, password_hash = ?, require_new_password = ? WHERE name = ?",

    # MARK: Profile

    "create_profile": """
        INSERT INTO Profiles (
            user_id,
            description,
            image_asset_id,
            banner_asset_id
        ) VALUES (?, '', NULL, NULL)""",

    "get_profile": """
        SELECT
            id,
            description,
            image_asset_id,
            banner_asset_id
        FROM Profiles
        WHERE user_id = ?
    """,

    "profile_exists": "SELECT EXISTS (SELECT user_id FROM Profiles WHERE user_id = ?)",

    "edit_profile": """
        UPDATE Profiles SET
            description = ?,
            image_asset_id = ?,
            banner_asset_id = ?
        WHERE user_id = ?
    """,

    # MARK: Asset

    "create_asset": "INSERT INTO Assets (filename, value) VALUES (?, ?)",

    "get_asset": "SELECT filename, value FROM Assets WHERE id = ?",

    "get_asset_with_submission_id": """
        SELECT
            id,
            filename,
            value
        FROM Assets
        WHERE id = (
            SELECT solution_asset_id FROM Submissions WHERE id = ?
        )
    """,

    "remove_asset": "DELETE FROM Assets WHERE id = ?",

    # MARK: Category

    "get_categories": "SELECT id, name FROM ChallengeCategories",

    # MARK: Challenge

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

    "create_challenge": """
        INSERT INTO Challenges (
            created,
            title,
            body,
            category_id,
            author_id,
            accepts_submissions
        ) VALUES (?, ?, ?, ?, ?, ?)
    """,

    "challenge_exists": "SELECT EXISTS (SELECT id FROM Challenges WHERE id = ?)",

    "edit_challenge": """
        UPDATE Challenges SET
            title = ?,
            body = ?,
            category_id = ?,
            accepts_submissions = ?
        WHERE id = ?
    """,

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
        WHERE 
            (? IS NULL OR C.category_id = ?)
            AND (
                LOWER(C.title) LIKE LOWER('%' || ? || '%') OR
                LOWER(C.body) LIKE LOWER('%' || ? || '%')
            )
        ORDER BY C.created DESC
        LIMIT ? OFFSET ?;
    """,

    # MARK: Vote

    "create_vote_for_challenge": "INSERT INTO Votes (challenge_id, voter_id) VALUES (?, ?)",
    
    "create_vote_for_comment": "INSERT INTO Votes (comment_id, voter_id) VALUES (?, ?)" ,

    "create_vote_for_submission": "INSERT INTO Votes (submission_id, voter_id) VALUES (?, ?)",

    "remove_vote_from_challenge": "DELETE FROM Votes WHERE challenge_id = ? AND voter_id = ?",

    "remove_vote_from_comment": "DELETE FROM Votes WHERE comment_id = ? AND voter_id = ?" ,

    "remove_vote_from_submission": "DELETE FROM Votes WHERE submission_id = ? AND voter_id = ?",

    # MARK: Vote stats

    "get_received_votes": """
        SELECT
            (SELECT COUNT(*) FROM Votes
            JOIN Challenges ON Votes.challenge_id = Challenges.id
            WHERE Challenges.author_id = ?) AS challenge_votes,

            (SELECT COUNT(*) FROM Votes
            JOIN Comments ON Votes.comment_id = Comments.id
            WHERE Comments.author_id = ?) AS comment_votes,

            (SELECT COUNT(*) FROM Votes
            JOIN Submissions ON Votes.submission_id = Submissions.id
            WHERE Submissions.author_id = ?) AS submission_votes;
    """,

    "get_given_votes": """
        SELECT
            (
            SELECT COUNT(*) FROM Votes
            WHERE voter_id = ? AND challenge_id IS NOT NULL) AS challenge_votes,

            (SELECT COUNT(*) FROM Votes
            WHERE voter_id = ? AND comment_id IS NOT NULL) AS comment_votes,

            (SELECT COUNT(*) FROM Votes
            WHERE voter_id = ? AND submission_id IS NOT NULL) AS submission_votes;
    """,

    # MARK: Comment

    "create_comment": "INSERT INTO Comments (created, challenge_id, body, author_id) VALUES (?, ?, ?, ?)",

    "get_comment":"""
        SELECT
            'comment' AS type,
            Comments.id,
            Comments.created,
            Comments.body,
            Comments.author_id,
            Users.username,
            Profiles.image_asset_id,
            (SELECT COUNT(*) FROM Votes WHERE comment_id = Comments.id) AS vote_count,
            EXISTS (
                SELECT 1 FROM Votes
                WHERE comment_id = Comments.id AND voter_id = ?
            ) AS has_voted,
            Comments.challenge_id
        FROM Comments
        JOIN Users ON Comments.author_id = Users.id
        LEFT JOIN Profiles ON Users.id = Profiles.user_id
        WHERE Comments.id = ?
    """,

    # MARK: Get Challenge replies
    "get_comments_and_submissions": """
        SELECT
            'comment' AS type,
            Comments.id,
            Comments.created,
            Comments.body,
            Comments.author_id,
            Users.username,
            Profiles.image_asset_id,
            (SELECT COUNT(*) FROM Votes WHERE comment_id = Comments.id) AS vote_count,
            EXISTS (
                SELECT 1 FROM Votes
                WHERE comment_id = Comments.id AND voter_id = ?
            ) AS has_voted,
            Comments.challenge_id,
            NULL AS solution_title,
            NULL AS solution_asset_id,
            NULL AS solution_filename
        FROM Comments
        JOIN Users ON Comments.author_id = Users.id
        LEFT JOIN Profiles ON Users.id = Profiles.user_id
        WHERE Comments.challenge_id = ?

        UNION ALL

        SELECT
            'submission' AS type,
            Submissions.id,
            Submissions.created,
            Submissions.body,
            Submissions.author_id,
            Users.username,
            Profiles.image_asset_id,
            (SELECT COUNT(*) FROM Votes WHERE submission_id = Submissions.id) AS vote_count,
            EXISTS (
                SELECT 1 FROM Votes
                WHERE submission_id = Submissions.id AND voter_id = ?
            ) AS has_voted,
            Submissions.challenge_id,
            Submissions.title,
            Submissions.solution_asset_id,
            Assets.filename AS solution_filename
        FROM Submissions
        JOIN Users ON Submissions.author_id = Users.id
        LEFT JOIN Profiles ON Users.id = Profiles.user_id
        JOIN Assets ON Submissions.solution_asset_id = Assets.id
        WHERE Submissions.challenge_id = ?

        ORDER BY created DESC
    """,

    "remove_comment": "DELETE FROM Comments WHERE id = ?",

    "comment_exists": "SELECT EXISTS (SELECT id FROM Comments WHERE id = ?)",

    "edit_comment": "UPDATE Comments SET body = ? WHERE id = ?",

    # MARK: Submission

    "create_submission": """
        INSERT INTO Submissions (
            created,
            challenge_id,
            title,
            body,
            solution_asset_id,
            author_id
        ) VALUES (?, ?, ?, ?, ?, ?)
    """,

    "remove_submission": "DELETE FROM Submissions WHERE id = ?",

    "get_submission":"""
        SELECT
            'submission' AS type,
            Submissions.id,
            Submissions.created,
            Submissions.body,
            Submissions.author_id,
            Users.username,
            Profiles.image_asset_id,
            (SELECT COUNT(*) FROM Votes WHERE submission_id = Submissions.id) AS vote_count,
            EXISTS (
                SELECT 1 FROM Votes
                WHERE submission_id = Submissions.id AND voter_id = ?
            ) AS has_voted,
            Submissions.challenge_id,
            Submissions.title,
            Submissions.solution_asset_id,
            Assets.filename AS solution_filename
        FROM Submissions
        JOIN Users ON Submissions.author_id = Users.id
        LEFT JOIN Profiles ON Users.id = Profiles.user_id
        JOIN Assets ON Submissions.solution_asset_id = Assets.id
        WHERE Submissions.id = ?
    """,

    "submission_exists": "SELECT EXISTS (SELECT id FROM Submissions WHERE id = ?)",

    "edit_submission": "UPDATE Submissions SET title = ?, body = ?, solution_asset_id = ? WHERE id = ?",

    # MARK: Get all user content
    
    "get_user_content": """
        SELECT
            'challenge' AS type,
            Challenges.id AS target_challenge_id,
            Challenges.id AS id,
            Challenges.created,
            Challenges.title,
            Challenges.body,
            Challenges.accepts_submissions,
            Challenges.category_id,
            ChallengeCategories.name AS category_name,
            Users.username AS author_name,
            Users.id AS author_id,
            Profiles.image_asset_id AS author_image_id,
            (SELECT COUNT(*) FROM Votes WHERE challenge_id = Challenges.id) AS votes,
            EXISTS (
                SELECT 1 FROM Votes
                WHERE challenge_id = Challenges.id AND voter_id = ?
            ) AS has_voted
        FROM Challenges
        JOIN ChallengeCategories ON Challenges.category_id = ChallengeCategories.id
        JOIN Users ON Challenges.author_id = Users.id
        LEFT JOIN Profiles ON Users.id = Profiles.user_id
        WHERE Challenges.author_id = ?

        UNION ALL

        SELECT
            'comment' AS type,
            Comments.challenge_id AS target_challenge_id,
            Comments.id,
            Comments.created,
            NULL AS title,
            Comments.body,
            NULL AS accepts_submissions,
            NULL AS category_id,
            NULL AS category_name,
            Users.username AS author_name,
            Users.id AS author_id,
            Profiles.image_asset_id AS author_image_id,
            (SELECT COUNT(*) FROM Votes WHERE comment_id = Comments.id) AS votes,
            EXISTS (
                SELECT 1 FROM Votes
                WHERE comment_id = Comments.id AND voter_id = ?
            ) AS has_votes
        FROM Comments
        JOIN Users ON Comments.author_id = Users.id
        LEFT JOIN Profiles ON Users.id = Profiles.user_id
        WHERE Comments.author_id = ?

        UNION ALL

        SELECT
            'submission' AS type,
            Submissions.challenge_id AS target_challenge_id,
            Submissions.id,
            Submissions.created,
            Submissions.title,
            Submissions.body,
            NULL AS accepts_submissions,
            NULL AS category_id,
            NULL AS category_name,
            Users.username AS author_name,
            Users.id AS author_id,
            Profiles.image_asset_id AS author_image_id,
            (SELECT COUNT(*) FROM Votes WHERE submission_id = Submissions.id) AS votes,
            EXISTS (
                SELECT 1 FROM Votes
                WHERE submission_id = Submissions.id AND voter_id = ?
            ) AS has_voted
        FROM Submissions
        JOIN Users ON Submissions.author_id = Users.id
        LEFT JOIN Profiles ON Users.id = Profiles.user_id
        WHERE Submissions.author_id = ?

        ORDER BY created DESC
    """
}
