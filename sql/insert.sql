INSERT INTO Role(user_role, role_name) VALUES
    (0, 'admin'),
    (1, 'user');

INSERT INTO Client(id, user_name, user_password, birthdate) VALUES
('ut', 'TEST_USER', '1234', CURRENT_TIMESTAMP); -- TODO delete before deploying!


INSERT INTO Genres (genre) VALUES
    ('Fantasy'),
    ('Science Fiction'),
    ('Adventure'),
    ('Romance'),
    ('Mystery'),
    ('Thriller');

INSERT INTO Authors(author) VALUES ('J. K. Rowling');

INSERT INTO Book(title, book_language, min_age, isbn, published, description, author_id, genre_id) VALUES
('Harry Potter and the Philosopher''s Stone', 'English', 6, 0000, 1997, 'good book', 1, 1),
('Harry Potter and the Goblet of Fire', 'English', 6, 0000, 2000, 'tragic book', 1, 1);

INSERT INTO Book_copy(book_id, book_location) VALUES
(1, 'Left'),
(1, 'Left'),
(1, 'Left'),
(1, 'Left'),
(2, 'Left');

CREATE USER a WITH PASSWORD '1234';
GRANT ALL PRIVILEGES ON DATABASE "bookManager" TO a;