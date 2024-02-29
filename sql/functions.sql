CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION insert_genre(name text) RETURNS INTEGER AS $$
    BEGIN
        INSERT INTO Genres(genre) VALUES (name);
        RETURN 0;
    END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION insert_author(name text) RETURNS INTEGER AS $$
    BEGIN
        INSERT INTO Authors(author) VALUES (name);
        RETURN 0;
    END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION insert_book(title text, lang varchar(20), age integer, isbn text, published integer,
                                        description text, book_cover text, author_id integer, genre_id integer) RETURNS INTEGER AS $$
    BEGIN
        INSERT INTO Book(title, book_language, min_age, isbn, published, description, book_cover, author_id, genre_id)
        VALUES (title, lang, age, isbn, published, description, book_cover, author_id, genre_id);
        RETURN 0;
    END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION insert_history (u_id text, b_id integer, l_date timestamp) RETURNS INTEGER AS $$
    BEGIN
        INSERT INTO History(user_id, book_id, loan_date)
        VALUES (u_id, b_id, l_date);
        RETURN 0;
    END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION insert_review(user_id text, book_id integer, rating integer) RETURNS INTEGER AS $$
    BEGIN
        INSERT INTO Reviews(user_id, book_id, rating)
        VALUES(user_id, book_id, rating);
        RETURN 0;
    END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION insert_book_copy(book_id integer, book_location TEXT) RETURNS INTEGER AS $$
    BEGIN
        INSERT INTO Book_copy(book_id, book_location)
        VALUES(book_id, book_location);
        RETURN 0;
    END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION insert_book_status(user_id text, book_id integer, copy_id integer) RETURNS INTEGER AS $$
    BEGIN
        -- loan end time is set my trigger
        INSERT INTO Book_status(user_id, book_id, copy_id, queue, loan_start, loan_end)
        VALUES(user_id, book_id, copy_id, FALSE, NOW(), NOW() + interval '30' day);
        RETURN 0;
    END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION has_queue_for_book(b_id integer, user_id text) RETURNS BOOLEAN AS $$
    DECLARE status integer;
    BEGIN
        status := (SELECT place_in_queue FROM book_queue WHERE book_id = b_id LIMIT 1);
        RETURN status;
    END;
$$ LANGUAGE plpgsql;

-- Loan a book if a copy of that book is available. Otherwise, return 1.
CREATE OR REPLACE FUNCTION loan_book(user_id text, b_id integer) RETURNS INTEGER AS $$
    DECLARE
        available_copy integer;
        was_loaned integer;
    BEGIN
        -- is there a queue for that book?
        IF has_queue_for_book(b_id, user_id) IS TRUE THEN
            -- is user on position 1, loan it 
            was_loaned := loan_and_update_queue(user_id, b_id);

            -- user was not on position 1 and book was was not loaned
            IF was_loaned = 1 THEN
                RAISE NOTICE 'Book is not available. Requested it.';
                PERFORM insert_queue(b_id, user_id);
                RETURN 1;
            END IF;
            RETURN 0;
        end if;

        -- to avoid WHERE NOT EXISTS? Slow?
        -- is book available?
        SELECT bc.copy_id
        INTO available_copy
        FROM Book_copy bc
        WHERE bc.book_id = b_id
            AND NOT EXISTS(
                SELECT bs.user_id
                FROM Book_status bs
                WHERE bc.copy_id = bs.copy_id)
        LIMIT 1;

        -- book is available
        IF available_copy IS NOT NULL THEN
            RAISE NOTICE 'Book is available.';
            PERFORM insert_book_status(user_id, b_id, available_copy);
            RETURN 0;
        ELSE -- book is not available
            RAISE NOTICE 'Book is not available. Requested it.';
            PERFORM insert_queue(b_id, user_id);
            RETURN 1;
        end if;

    END;
$$ LANGUAGE plpgsql;

-- TODO set the queue lock for that book?
CREATE OR REPLACE FUNCTION insert_queue (b_id integer, u_id text) RETURNS INTEGER AS $$
    DECLARE queue_place integer;
    BEGIN
        queue_place := (SELECT MAX(place_in_queue) FROM Book_queue AS bq WHERE bq.book_id = b_id);
        -- no one is in the queue for that book yet
        IF queue_place IS NULL THEN
            queue_place = 0;
        end if;

        -- this user is already in the queue for that book
        IF EXISTS (SELECT 0 FROM book_queue WHERE book_id = b_id AND user_id = u_id) THEN
            RAISE NOTICE 'This user is already in the queue for that book.';
        ELSE -- enter the queue
            INSERT INTO Book_queue(book_id, user_id, place_in_queue)
            VALUES (b_id, u_id, (queue_place+1));
        END IF;
        RETURN 0;
    END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION return_book(c_id integer) RETURNS INTEGER AS $$
    DECLARE returned record;
    DECLARE next_queue_pos integer;
    DECLARE next_in_queue record;
    BEGIN
        SELECT bs.user_id, bs.book_id, bs.loan_start
        INTO returned
        FROM Book_status AS bs
        WHERE bs.copy_id = c_id;

        -- remove it from the list of current loans
        DELETE FROM Book_status AS bs
        WHERE bs.copy_id = c_id;

        -- add it to user history
        PERFORM insert_history(returned.user_id, returned.book_id, returned.loan_start);

        -- give book to next user in the queue
        SELECT MIN(place_in_queue)
        INTO next_queue_pos
        FROM Book_queue bq
        WHERE bq.book_id = returned.book_id;

        IF next_queue_pos IS NOT NULL THEN
            -- get queue entry
            SELECT *
            INTO next_in_queue
            FROM book_queue bc
                WHERE bc.book_id = returned.book_id
                AND bc.place_in_queue = next_queue_pos;

            -- TODO notify user
            RAISE NOTICE 'Requested book is now available (user: %, book: %).',
                next_in_queue.user_id, next_in_queue.book_id ;
        end if;

        RETURN 0;
    END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION extend_loan(user_i text, book integer, copy integer) RETURNS INTEGER AS $$
    BEGIN
        -- no queue for that book
        IF has_queue_for_book(book, user_i) IS NULL THEN
            UPDATE Book_Status SET loan_end = NOW() + interval '15' day,
                                   times_renewed = times_renewed + 1
            WHERE user_id = user_i AND copy_id = copy;

        ELSE RAISE NOTICE 'Not able to extend loan due to current queue';
        END IF;
        RETURN 0;
    END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION loan_and_update_queue(user_i text, book integer) RETURNS INTEGER AS $$
    DECLARE position integer;
    BEGIN
        SELECT bq.place_in_queue
            INTO position
            FROM book_queue AS bq
            WHERE bq.book_id = book AND bq.user_id = user_i;

        IF position = 1 THEN
            PERFORM insert_book_status(user_i, book, check_if_copy_is_available(book));
            DELETE FROM book_queue WHERE user_id = user_i AND book_id = book;
            UPDATE book_queue SET place_in_queue = place_in_queue - 1 WHERE book_id = book;
            RETURN 0;
        END IF;
        RETURN 1;
    END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION check_if_copy_is_available(book integer) RETURNS INTEGER AS $$
    DECLARE avalible_copy integer;
    BEGIN
        SELECT bc.copy_id
            INTO avalible_copy
            FROM book_copy AS bc
            WHERE bc.book_id = book
                AND NOT EXISTS(
                    SELECT bs.user_id
                    FROM Book_status bs
                    WHERE bc.copy_id = bs.copy_id)
            LIMIT 1;
        RETURN avalible_copy;
    END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION euclidean_distance(a FLOAT[], b FLOAT[])
RETURNS FLOAT AS $$
DECLARE
    sum FLOAT := 0.0;
BEGIN
    FOR i IN 1..array_length(a, 1) LOOP
        sum := sum + (a[i] - b[i]) * (a[i] - b[i]);
    END LOOP;
    RETURN sqrt(sum);
END;
$$ LANGUAGE plpgsql;
