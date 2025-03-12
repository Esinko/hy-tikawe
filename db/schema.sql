-- Assets and attachments
CREATE TABLE assets (
    id INTEGER PRIMARY KEY,
    filename TEXT UNIQUE NOT NULL,
    value BLOB NOT NULL
);

CREATE TABLE attachments ( -- Challenges can have many assets
    challenge_id INTEGER PRIMARY KEY
    attachment_id INTEGER REFERENCES assets
    FOREIGN KEY (challenge_id) REFERENCES challenges(id) ON DELETE CASCADE
)

-- User Data
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    require_new_password BOOLEAN
);

CREATE TABLE profiles (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users NOT NULL,
    description TEXT,
    profile_image_asset_id INTEGER REFERENCES assets,
    FOREIGN KEY (profile_image_asset_id) REFERENCES assets(id) ON DELETE CASCADE
    profile_banner_asset_id INTEGER REFERENCES assets
    FOREIGN KEY (profile_banner_asset_id) REFERENCES assets(id) ON DELETE CASCADE
);

-- Challenge categories
CREATE TABLE challenge_categories (
    id INTEGER PRIMARY KEY,
    name TEXT
)

-- Challenges, submissions and comments
CREATE TABLE challenges (
    id INTEGER PRIMARY KEY,
    created INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    category INTEGER NOT NULL,
    FOREIGN KEY (category) REFERENCES challenge_categories(id) ON DELETE CASCADE
    author_id INTEGER NOT NULL
    FOREIGN KEY (author_id) REFERENCES users(id)
)

CREATE TABLE submissions (
    id INTEGER PRIMARY KEY,
    created INTEGER NOT NULL,
    challenge_id INTEGER NOT NULL
    FOREIGN KEY (challenge_id) REFERENCES challenges(id) ON DELETE CASCADE
    title TEXT NOT NULL,
    body TEXT NOT NULL
    solution_asset_id INTEGER NOT NULL
    FOREIGN KEY (solution_asset_id) REFERENCES assets(id) ON DELETE CASCADE
    author_id INTEGER NOT NULL
)

CREATE TABLE comments (
    id INTEGER PRIMARY KEY,
    created INTEGER NOT NULL,
    challenge_id INTEGER NOT NULL
    FOREIGN KEY (challenge_id) REFERENCES challenges(id) ON DELETE CASCADE
    body TEXT NOT NULL
    author_id INTEGER NOT NULL
    FOREIGN KEY (author_id) REFERENCES users(id)
)

-- Votes, 3 possible references
CREATE TABLE votes (
    id INTEGER PRIMARY KEY
    id INTEGER PRIMARY KEY,
    challenge_id INTEGER REFERENCES challenges(id) ON DELETE CASCADE,
    submission_id INTEGER REFERENCES submissions(id) ON DELETE CASCADE,
    comment_id INTEGER REFERENCES comments(id) ON DELETE CASCADE,
    CHECK (
        (challenge_id IS NOT NULL AND submission_id IS NULL AND comment_id IS NULL) OR
        (challenge_id IS NULL AND submission_id IS NOT NULL AND comment_id IS NULL) OR
        (challenge_id IS NULL AND submission_id IS NULL AND comment_id IS NOT NULL)
    )
)