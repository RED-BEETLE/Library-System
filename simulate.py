import string
import psycopg2
import random
import datetime
import csv
from sentence_transformers import SentenceTransformer, util
model = SentenceTransformer('all-MiniLM-L6-v2')
# import bcrypt

NUM_DAYS = 30
NUM_CLIENTS = 200
MAX_LOANS_IN_A_DAY = 50
MAX_RETURNS_IN_A_DAY = 30
MAX_EXTENSIONS_IN_A_DAY = 15
MAX_REVIEWS_IN_A_DAY = 100
MAX_NR_COPIES = 5

connection = psycopg2.connect(
    database="bookManager",
    user="a",
    password="1234",
    host="localhost",
    port='5432')

connection.set_session(autocommit=True)
cursor = connection.cursor()


def create_users():
    start_date = datetime.date(1920, 1, 1)
    end_date = datetime.date(2022, 1, 1)
    first_names = ['William', 'Mia', 'Björn', 'Henrik', 'Anna', 'Mikael', 'Stig', 'Petra', 'Elin', 'Emil']
    last_names = ['Karlsson', 'Nilsson', 'Olsson', 'Persson', 'Svensson', 'Gustafsson', 'Johansson',
                  'Petersson', 'Bengtsson', 'Eriksson']

    for i in range(0, NUM_CLIENTS):
        password = ''.join(random.choice(string.ascii_letters) for _ in range(10))
        # hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        # pw_hash = hashed_password.decode('utf-8')
        random_birthday = start_date + (end_date - start_date) * random.random()
        name = random.choice(first_names) + random.choice(last_names)
        try:
            cursor.execute(f"""
                            INSERT INTO Client(id, user_name, user_password, birthdate)
                            VALUES ('{name + str(random.randint(1, 10000)) + '@email.com'}',' 
                            {name}',' {password}',' {random_birthday}')""")
        except Exception:
            continue


def add_books_to_library():
    with open("4000books.csv", 'r', newline='') as book_file:
        csvreader = csv.reader(book_file, delimiter='\n')
        next(csvreader)  # To skip header

        for row in csvreader:
            book_to_add = row
            book_split = book_to_add[0].split(';')

            # Add author
            author = book_split[2]
            author = author.replace('"', '')
            insert_author(author)

            # Get author id
            cursor.execute("SELECT author_id FROM Authors WHERE author = %s", (author,))
            author_id = cursor.fetchall()
            author_id = author_id[0]

            # Add book and copies of book
            insert_book(book_split, author_id[0])


def insert_book(book_split, author):
    languages = ['English', 'Swedish', 'Spanish', 'French', 'German']
    descriptions = ['amusing', 'mysterious', 'adventurous', 'surprising', 'unique', 'informative', 'fictional']

    title = book_split[1]
    title = title.replace('"', '')
    language = random.choice(languages)
    age = random.randint(0, 18)
    isbn = book_split[0]
    published = book_split[3]
    published = published.replace('"', '')
    description = random.choice(descriptions) + ' book'
    cover = book_split[7]
    cover = cover.replace('"', '')

    cursor.execute("SELECT genre_id, genre FROM Genres ORDER BY RANDOM() LIMIT 1")
    genres = cursor.fetchall()
    genre = genres[0][0]
    genre_name = genres[0][1]
    sentence = title + " " + str(age) + " " + language + " " + description + " " + genre_name

    try:
        # Add book
        cursor.callproc('insert_book', (title, language, age, isbn, published, description, cover, author, genre), )

        # Create book copies
        for i in range(0, random.randint(2, MAX_NR_COPIES)):
            cursor.execute("SELECT id FROM Book WHERE title = %s ", (title,))
            book_id = cursor.fetchall()
            book_id = book_id[0]
            location = random.choice(string.ascii_uppercase)
            cursor.callproc('insert_book_copy', (book_id[0], location + str(random.randint(0, 9))), )

        # Add embedding
        embedding = model.encode(sentence).tolist()
        cursor.execute("INSERT INTO book_embedding (book_id, embedding) VALUES (%s, %s)", (book_id, embedding))
        connection.commit()

    except Exception:
        pass


def insert_author(author):
    author = author.replace('"', '')
    try:
        cursor.callproc('insert_author', [author, ])
    except Exception:
        pass


def loan_from_queue():
    cursor.execute("SELECT user_id, book_id FROM book_queue WHERE place_in_queue = 1;")
    first_in_queue = cursor.fetchall()
    for i in first_in_queue:
        var = i
        try:
            cursor.callproc('loan_and_update_queue', (var[0], var[1]), )
        except Exception:
            continue


def simulate():
    for i in range(0, NUM_DAYS):
        # Loans books that are available to first person in the queue
        loan_from_queue()

        # Random user borrows random book from random library
        for j in range(0, random.randint(0, MAX_LOANS_IN_A_DAY)):
            cursor.execute("SELECT id FROM Client ORDER BY RANDOM() LIMIT 1")
            u_id = cursor.fetchall()
            cursor.execute("SELECT id FROM Book ORDER BY RANDOM() LIMIT 1")
            b_id = cursor.fetchall()
            try:
                cursor.callproc('loan_book', (u_id[0], b_id[0]), )
            except Exception:
                continue

        # extend loan time for random book
        for j in range(0, random.randint(0, MAX_EXTENSIONS_IN_A_DAY)):
            try:
                cursor.execute("SELECT copy_id FROM Book_status ORDER BY RANDOM() LIMIT 1")
                c_id = cursor.fetchall()
                c_id = c_id[0]
                cursor.execute("SELECT user_id FROM Book_status WHERE copy_id = %s ORDER BY RANDOM() LIMIT 1",
                               (c_id[0],))
                u_id = cursor.fetchall()
                u_id = u_id[0]
                cursor.execute("SELECT book_id FROM Book_status WHERE copy_id = %s ORDER BY RANDOM() LIMIT 1",
                               (c_id[0],))
                b_id = cursor.fetchall()
                b_id = b_id[0]
                cursor.callproc('extend_loan', (u_id[0], b_id[0], c_id[0]), )
            except Exception:
                continue

        # return random book
        for j in range(0, random.randint(0, MAX_RETURNS_IN_A_DAY)):
            cursor.execute("SELECT copy_id FROM Book_status ORDER BY RANDOM() LIMIT 1")
            c_id = cursor.fetchall()
            try:
                cursor.callproc('return_book', (c_id[0]), )
            except Exception:
                continue

        # Random user leaves review on a random book, if the user already
        # left a review on the book the old review is updated
        for j in range(0, random.randint(0, MAX_REVIEWS_IN_A_DAY)):

            cursor.execute("SELECT id FROM Client ORDER BY RANDOM() LIMIT 1")
            u_id = cursor.fetchall()
            u_id = u_id[0]
            u_id = u_id[0]
            cursor.execute("SELECT id FROM Book ORDER BY RANDOM() LIMIT 1")
            b_id = cursor.fetchall()
            b_id = b_id[0]
            b_id = b_id[0]
            cursor.execute("SELECT * FROM Reviews WHERE user_id = %s AND book_id = %s "
                           "ORDER BY RANDOM() LIMIT 1", (u_id, b_id, ))
            review = cursor.fetchall()

            if len(review) == 0:
                cursor.callproc('insert_review', (u_id, b_id, random.randint(1, 5)), )
            else:
                new_rating = random.randint(1, 5)
                cursor.execute("UPDATE Reviews SET rating = %s "
                               "WHERE user_id = %s AND book_id = %s", (new_rating, u_id, b_id, ))


create_users()
add_books_to_library()
simulate()