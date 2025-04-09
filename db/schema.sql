-- Assets and attachments
CREATE TABLE Assets (
    id INTEGER PRIMARY KEY,
    filename TEXT NOT NULL,
    value BLOB NOT NULL
);

CREATE TABLE Attachments ( -- Challenges can have many assets
    id INTEGER PRIMARY KEY,
    challenge_id INTEGER NOT NULL REFERENCES Challenges(id),
    asset_id INTEGER NOT NULL REFERENCES Assets(id)
);

-- User Data
CREATE TABLE Users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    require_new_password INTEGER NOT NULL DEFAULT 0,
    is_admin INTEGER NOT NULL DEFAULT 0,
    UNIQUE(username)
);

CREATE TABLE Profiles (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    description TEXT,
    image_asset_id INTEGER REFERENCES Assets(id),
    banner_asset_id INTEGER REFERENCES Assets(id)
);

-- Challenge categories
CREATE TABLE ChallengeCategories (
    id INTEGER PRIMARY KEY,
    name TEXT
);

-- Challenges, submissions and comments
CREATE TABLE Challenges (
    id INTEGER PRIMARY KEY,
    created INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    category_id INTEGER NOT NULL REFERENCES ChallengeCategories(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES Users(id),
    accepts_submissions INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE Submissions (
    id INTEGER PRIMARY KEY,
    created INTEGER NOT NULL,
    challenge_id INTEGER NOT NULL REFERENCES Challenges(id),
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    solution_asset_id INTEGER NOT NULL REFERENCES Assets(id),
    author_id INTEGER NOT NULL
);

CREATE TABLE Comments (
    id INTEGER PRIMARY KEY,
    created INTEGER NOT NULL,
    challenge_id INTEGER NOT NULL REFERENCES Challenges(id),
    body TEXT NOT NULL,
    author_id INTEGER NOT NULL REFERENCES Users(id)
);

-- Votes, 3 possible references
CREATE TABLE Votes (
    id INTEGER PRIMARY KEY,
    challenge_id INTEGER REFERENCES Challenges(id) ON DELETE CASCADE,
    submission_id INTEGER REFERENCES Submissions(id) ON DELETE CASCADE,
    comment_id INTEGER REFERENCES Comments(id) ON DELETE CASCADE,
    voter_id INTEGER REFERENCES Users(id) ON DELETE CASCADE,
    CHECK (
        (challenge_id IS NOT NULL AND submission_id IS NULL AND comment_id IS NULL) OR
        (challenge_id IS NULL AND submission_id IS NOT NULL AND comment_id IS NULL) OR
        (challenge_id IS NULL AND submission_id IS NULL AND comment_id IS NOT NULL)
    ),
    UNIQUE(voter_id, challenge_id),
    UNIQUE(voter_id, submission_id),
    UNIQUE(voter_id, comment_id)
);

-- Count votes per challenge
CREATE INDEX votes_challenge_id ON Votes(challenge_id)
WHERE challenge_id IS NOT NULL;

-- Count votes per submission
CREATE INDEX votes_submission_id ON Votes(submission_id)
WHERE submission_id IS NOT NULL;

-- Count votes per comment
CREATE INDEX votes_comment_id ON Votes(comment_id)
WHERE comment_id IS NOT NULL;

-- Count votes per challenge from specific voter
CREATE INDEX votes_challenge_voter ON Votes(challenge_id, voter_id)
WHERE challenge_id IS NOT NULL;

-- Count votes per comment from specific voter
CREATE INDEX votes_comment_voter ON Votes(comment_id, voter_id)
WHERE comment_id IS NOT NULL;

-- Count votes per submission from specific voter
CREATE INDEX votes_submission_voter ON Votes(submission_id, voter_id)
WHERE submission_id IS NOT NULL;

-- Optimize matching thing id to author id (important for counting total votes for a user)
CREATE INDEX challenge_id_to_author_id ON Challenges(id, author_id);
CREATE INDEX comment_id_to_author_id ON Comments(id, author_id);
CREATE INDEX submission_id_to_author_id ON Submissions(id, author_id);
