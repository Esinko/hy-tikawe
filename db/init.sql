-- Clear database
DELETE FROM ChallengeCategories;
DELETE FROM Assets;
DELETE FROM Attachments;
DELETE FROM Users;
DELETE FROM Profiles;
DELETE FROM Challenges;
DELETE FROM Submissions;
DELETE FROM Comments;
DELETE FROM Votes;
DELETE FROM VoteCounts;

-- Default categories
INSERT INTO ChallengeCategories (name) VALUES ("Least Lines of Javascript");
INSERT INTO ChallengeCategories (name) VALUES ("One Line of Javascript");
INSERT INTO ChallengeCategories (name) VALUES ("No Variable Declaration");

-- Create admin account
INSERT INTO Users (id, username, password_hash, require_new_password) VALUES (0, "admin", "scrypt:32768:8:1$9YEUjvYO6LxacZfR$43915005f88112dff2ffd39726713e435aedcaa71a8e6e136f40c9edcd69ae16ba0a42691eef880a59c7fb14bac21e184cd9ad7a929e9fb4f445f65fbe6ae19e", True);
INSERT INTO Profiles (id, user_id, description) VALUES (0, 0, "He who remains");
