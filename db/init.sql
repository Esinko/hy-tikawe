-- Clear database
DELETE FROM challenge_categories;
DELETE FROM assets;
DELETE FROM attachments;
DELETE FROM users;
DELETE FROM profiles;
DELETE FROM challenges;
DELETE FROM submissions;
DELETE FROM comments;
DELETE FROM votes;

-- Default categories
INSERT INTO challenge_categories (name) VALUES ("Least Lines of Javascript");
INSERT INTO challenge_categories (name) VALUES ("One Line of Javascript");
INSERT INTO challenge_categories (name) VALUES ("No Variable Declaration");

-- Create admin account
INSERT INTO users (id, username, password_hash, require_new_password) VALUES (0, "admin", "", True);
INSERT INTO profiles (id, user_id, description) VALUES (0, 0, "He who remains");
