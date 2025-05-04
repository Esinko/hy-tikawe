-- Clear database
DELETE FROM ChallengeCategories;
DELETE FROM Assets;
DELETE FROM Users;
DELETE FROM Profiles;
DELETE FROM Challenges;
DELETE FROM Submissions;
DELETE FROM Comments;
DELETE FROM Votes;

-- Default categories
INSERT INTO ChallengeCategories (name) VALUES ("General");
INSERT INTO ChallengeCategories (name) VALUES ("Least Lines of Javascript");
INSERT INTO ChallengeCategories (name) VALUES ("One Line of Javascript");
INSERT INTO ChallengeCategories (name) VALUES ("No Variable Declaration");

-- Create admin account
INSERT INTO Users (id, username, password_hash, require_new_password, is_admin) VALUES (0, "admin", "scrypt:32768:8:1$9YEUjvYO6LxacZfR$43915005f88112dff2ffd39726713e435aedcaa71a8e6e136f40c9edcd69ae16ba0a42691eef880a59c7fb14bac21e184cd9ad7a929e9fb4f445f65fbe6ae19e", 1, 1);
INSERT INTO Profiles (id, user_id, description) VALUES (0, 0, "He who remains");

-- Create dummy chat message
INSERT INTO Challenges (id, created, title, body, category_id, author_id) VALUES(0, 0, "Welcome", "Welcome to the forum! Sadly not written in a single line of JavaScript :(", 1, 0);

-- Create dummy challenges
INSERT INTO Challenges (id, created, title, body, category_id, author_id) VALUES
    (1, 1733725672, "Hello World?", "Make JavaScript output 'Hello, World!' without using any letters. Yes, really.", 2, 0),
    (2, 1736174362, "Math Only", "Can you print the alphabet using only math operations?", 2, 0),
    (4, 1742470195, "Zero Declarations", "Make a working to-do list app without declaring a single variable. We’re not joking.", 3, 0),
    (6, 1726645716, "Unicode Magic", "Create a function that prints your code's source using only weird Unicode characters.", 2, 0),
    (7, 1724477332, "Callback Hell", "Nested callbacks only. No promises. No async/await. Go as deep as you dare.", 4, 0);

