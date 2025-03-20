-- Assets and attachments
CREATE TABLE Assets (
    id INTEGER PRIMARY KEY,
    filename TEXT NOT NULL,
    value BLOB NOT NULL
);

CREATE TABLE Attachments ( -- Challenges can have many assets
    id INTEGER PRIMARY KEY,
    challenge_id INTEGER NOT NULL REFERENCES Challenges(id) ON DELETE CASCADE,
    asset_id INTEGER NOT NULL REFERENCES Assets(id)
);

-- User Data
CREATE TABLE Users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    require_new_password INTEGER NOT NULL DEFAULT 0
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
    category INTEGER NOT NULL REFERENCES ChallengeCategories(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES Users(id)
);

CREATE TABLE Submissions (
    id INTEGER PRIMARY KEY,
    created INTEGER NOT NULL,
    challenge_id INTEGER NOT NULL REFERENCES Challenges(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    solution_asset_id INTEGER NOT NULL REFERENCES Assets(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL
);

CREATE TABLE Comments (
    id INTEGER PRIMARY KEY,
    created INTEGER NOT NULL,
    challenge_id INTEGER NOT NULL REFERENCES Challenges(id) ON DELETE CASCADE,
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
    )
);

CREATE TABLE VoteCounts ( -- Once and a while updated count based on the votes
    challenge_id INTEGER REFERENCES Challenges(id) ON DELETE CASCADE,
    submission_id INTEGER REFERENCES Submissions(id) ON DELETE CASCADE,
    comment_id INTEGER REFERENCES Comments(id) ON DELETE CASCADE,
    count INTEGER NOT NULL,
    CHECK (
        (challenge_id IS NOT NULL AND submission_id IS NULL AND comment_id IS NULL) OR
        (challenge_id IS NULL AND submission_id IS NOT NULL AND comment_id IS NULL) OR
        (challenge_id IS NULL AND submission_id IS NULL AND comment_id IS NOT NULL)
    )
);