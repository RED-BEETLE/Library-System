DROP TABLE IF EXISTS Book;
DROP TABLE IF EXISTS Role;
DROP TABLE IF EXISTS Client;
DROP TABLE IF EXISTS History;
DROP TABLE IF EXISTS Reviews;
DROP TABLE IF EXISTS Genres;
DROP TABLE IF EXISTS Authors;
DROP TABLE IF EXISTS Book_copy;
DROP TABLE IF EXISTS Book_status;
DROP TABLE IF EXISTS Book_queue;
DROP TABLE IF EXISTS Library;
DROP TABLE IF EXISTS Book_embedding;

CREATE TABLE Authors (
    author_id SERIAL PRIMARY KEY,
    author TEXT UNIQUE NOT NULL
);

CREATE TABLE Genres (
    genre_id SERIAL PRIMARY KEY,
    genre TEXT NOT NULL
);

CREATE TABLE Book (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    book_language VARCHAR(20),
    min_age SMALLINT,
    isbn TEXT,
    published SMALLINT,
    description TEXT,
    book_cover TEXT,
    author_id SERIAL,
    genre_id SERIAL,
    FOREIGN KEY (author_id) REFERENCES Authors(author_id),
    FOREIGN KEY (genre_id) REFERENCES Genres(genre_id)
);

CREATE TABLE Role (
    user_role SMALLINT PRIMARY KEY DEFAULT '1',
    role_name TEXT
);

CREATE TABLE Client (
    id TEXT PRIMARY KEY, -- email address
    user_name TEXT NOT NULL,
    user_password VARCHAR(512) NOT NULL,
    birthdate TIMESTAMP NOT NULL,
    user_role SMALLINT DEFAULT '1',
    FOREIGN KEY(user_role) REFERENCES Role(user_role)
);

CREATE TABLE History (
    history_id SERIAL PRIMARY KEY,
    user_id TEXT,
    book_id SERIAL,
    loan_date TIMESTAMP NOT NULL,
    return_date TIMESTAMP DEFAULT now(),
    FOREIGN KEY (user_id) REFERENCES Client(id),
    FOREIGN KEY (book_id) REFERENCES Book(id)
);

CREATE TABLE Reviews (
    user_id TEXT,
    book_id SERIAL,
    rating SMALLINT check (rating>0 AND rating<6) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Client(id),
    FOREIGN KEY (book_id) REFERENCES Book(id),
    PRIMARY KEY (user_id, book_id)
);

CREATE TABLE Book_copy (
    copy_id SERIAL PRIMARY KEY,
    book_id SERIAL,
    book_location TEXT,
    FOREIGN KEY (book_id) REFERENCES Book(id)
);

CREATE TABLE Book_status (
    user_id TEXT,
    book_id SERIAL,
    copy_id SERIAL,
    loan_start TIMESTAMP DEFAULT now(),
    loan_end TIMESTAMP,
    queue BOOLEAN NOT NULL, -- TODO check :)
    times_renewed SMALLINT DEFAULT '0',
    FOREIGN KEY (user_id) REFERENCES Client(id),
    FOREIGN KEY (book_id) REFERENCES Book(id),
    FOREIGN KEY (copy_id) REFERENCES Book_copy(copy_id),
    PRIMARY KEY (user_id, copy_id)
);

CREATE TABLE Book_queue (
    book_id SERIAL,
    user_id TEXT,
    place_in_queue SMALLINT NOT NULL,
    FOREIGN KEY (book_id) REFERENCES Book(id),
    FOREIGN KEY (user_id) REFERENCES Client(id),
    PRIMARY KEY (book_id, user_id)
);


CREATE TABLE Book_embedding (
    book_id SERIAL PRIMARY KEY,
    embedding FLOAT[] NOT NULL,
    FOREIGN KEY (book_id) REFERENCES Book(id)
);
