# Import regex module for backend input-validation from request-headers (for non-frontend-called (i.e. frontend validation won't be present then), 
# intercepted/'direct' API-requests)
import re
import json # Module to read JSON objects, and convert them to usable JS-objects
import requests # To match fetch-requests to some API with Python :)

import random # Module to generate random values

# Import Flask Class/Module/Library
from flask import Flask, jsonify, request

# For Environment Variables:
import os 
from dotenv import load_dotenv 

load_dotenv(dotenv_path=".dbenv")

# Import 'psycopg2' Module to Connect Database to our Flask-Python Backend
import psycopg2

# Module for hashing passwords
import bcrypt

# So my frontend can make API-calls to my backend
from flask_cors import CORS

from collections import OrderedDict

# Create Flask App (i.e. 'backend server/router')
app = Flask(__name__)
CORS(app)

connection_string = f"""gssencmode=disable user={os.getenv("SUPABASE_USER")} password={os.getenv("SUPABASE_PASSWORD")} 
                        host={os.getenv("SUPABASE_HOST")} port={os.getenv("SUPABASE_PORT")} 
                        dbname={os.getenv("SUPABASE_DB_NAME")}"""

conn = psycopg2.connect(connection_string)
cursor = conn.cursor()

CREATE_ROLES_TABLE = (
    "CREATE TABLE IF NOT EXISTS roles (role_id SERIAL PRIMARY KEY, role_name VARCHAR(50) NOT NULL);"
)
# ! Extract the user’s role_id (either from their JWT TOKEN, session, or request headers).

CREATE_PERMISSIONS_TABLE = (
    """ 
        CREATE TABLE IF NOT EXISTS permissions (
            role_id INT REFERENCES roles(role_id) NOT NULL, -- foreign key that RELATIONALLY Links the permissions_table to the roles_table
            table_name TEXT NOT NULL, 
            action TEXT NOT NULL, -- 'SELECT', 'INSERT', 'UPDATE', 'DELETE'
            column_field TEXT NOT NULL, -- the specific column the user can perform this action on | '*' === access to entire table of row-entries for this action (i.e. Librarian-Admin)
            PRIMARY KEY (role_id, table_name, action, column_field) -- ensure all permission-combinations are unique
        ); 
    """
)

# Users: Unique-StudentID (Primary Key; 9 digits; input validation when logging in via Regex) | is_activated_account | books_checked_out | books_overdue |
CREATE_USERS_TABLE = (
    """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY, -- Unique user identifier for the table (hence SERIAL | unrelated to input)
            role_id INT REFERENCES roles(role_id) NOT NULL, -- Foreign key to roles table | To RELATIONALLY link each user to their role
            user_id TEXT NOT NULL UNIQUE, -- ID specific to the role (StudentID or LibrarianID)
            user_name TEXT NOT NULL, -- username
            password_hash BYTEA NOT NULL, -- password for the user (hashed for security) [bytea-format]
            is_active_account BOOLEAN NOT NULL DEFAULT FALSE, -- account is approved / is allowed to check-out books (i.e. <=3 books overdue) [not deactivated / DE-PROVISIONED by the librarian-admin]
            books_overdue TEXT[],   -- DEFAULT ARRAY[]::TEXT[] (book_isbn_id == Text)
                                    -- array/list of all books (book_id's for uniqueness) the user has overdue (i.e. not returned in >=1 month)
                                    -- * if the user exceeds 3 books simultaneously overdue,
                                    -- * all librarian-admin-role-users will be notified,
                                    -- * and they can DE-PROVISION (i.e. set 'is_active_account:False')
                                    -- * this user, to prevent them from being able to borrow-books again.
                                    -- * for the user, they will still be able to view books, but when it comes
                                    -- to borrowing books (i.e., checking them out), the 'borrow book' button
                                    -- in the frontend will be grayed out, and the user will be displayed
                                    -- an error that 'Your account has been deactivated. You many not check out 
                                    -- any books, until you return your overdue books.' error-message.
                                    -- NOTE: We are storing the books themselves in 'books_overdue' (as the book_ids for uniqueness),
                                    -- not just the count, since, when the user returns a book, we want to be able to check if 
                                    -- that book was overdue (i.e. in the 'books_overdue' list) — that way, we can remove
                                    -- it from the books_overdue list as well [else, with a simple count, we wouldn't
                                    -- know which books exactly were overdue, and would have to recompute that for 
                                    -- every book to decide [INEFFICIENT]].
            string_password_hash TEXT NOT NULL -- string representation of hashed password cipher-text
        );                        
    """
)

CREATE_BOOKS_TABLE = (
    """ 
        CREATE TABLE IF NOT EXISTS books (
            book_isbn_id TEXT NOT NULL PRIMARY KEY, 
            title TEXT NOT NULL, 
            author TEXT NOT NULL, 
            published_year INT NOT NULL,
            total_book_count INT NOT NULL, 
            available_count INT NOT NULL
        ); 
    """
)

# MANY-TO-MANY RELATIONSHIPS (i.e. 1 table references the other [foreign-key]...)
CREATE_USER_BOOK_CHECKOUTS_TABLE = (

    """
        CREATE TABLE IF NOT EXISTS user_book_checkouts (
            user_id TEXT REFERENCES users(user_id),
            book_isbn_id TEXT REFERENCES books(book_isbn_id),
            checkout_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, book_isbn_id) -- to ensure unique combinations of (lib_id, book_id) [i.e. no repeats of this exact combination]
        );
    """  
)

# Create Initial Roles Table (Roles: Librarian (1), Student (2))
def setStaticRolesTable():
    cursor.execute(CREATE_ROLES_TABLE) 
    cursor.execute("SELECT COUNT(*) FROM roles;")

    row_count = cursor.fetchone()[0]

    if row_count == 0:
        cursor.execute("INSERT INTO roles (role_name) VALUES ('librarian');")
        cursor.execute("INSERT INTO roles (role_name) VALUES ('student');")
        conn.commit() # Commit this change to GIT in supabase
        print("Initial Roles Table Created. Inserted Librarian-Admin + Student Roles, & Enabled Row-Level Security.") 
 

# Create Initial Permissions Table (Librarian-Admins, Students have different permissions)
def setStaticPermissionsTable():
    cursor.execute(CREATE_PERMISSIONS_TABLE) 
    cursor.execute("SELECT COUNT(*) FROM permissions;")

    row_count = cursor.fetchone()[0]

    if row_count == 0:
        librarian_permissions = [('users', 'DELETE', "N/A"), ('users', 'UPDATE', 'is_active_account'), ('users', 'SELECT', '*'), ('books', 'SELECT', '*'), ('books', 'INSERT',  "N/A"), ('books', 'DELETE',  "N/A"), ('books', 'UPDATE', "book_isbn_id"), ('books', 'UPDATE', "title"), ('books', 'UPDATE', "author"), ('books', 'UPDATE', "published_year"), ('books', 'UPDATE', "total_book_count"), ('books', 'UPDATE', "available_count")] # List of Librarian Permission_Tuples: (Table_Name, Action)
        student_permissions =  [('books', 'SELECT', '*'), ('books', 'UPDATE', 'available_count'), ('user_book_checkouts', 'INSERT',  "N/A"), ('user_book_checkouts', 'DELETE',  "N/A")] # List of Student Permission_Tuples: (Table_Name, Action, Column_Field)

        # For "Books, Update, Null": Librarians can update WHATEVER field of the book they like (no column specified)
        for lib_permission in librarian_permissions:
            cursor.execute("INSERT INTO permissions (role_id, table_name, action, column_field) VALUES (%s, %s, %s, %s);", (1, lib_permission[0], lib_permission[1], lib_permission[2],))
            conn.commit() # Commit this change to GIT in supabase

        for stud_permission in student_permissions:
            cursor.execute("INSERT INTO permissions (role_id, table_name, action, column_field) VALUES (%s, %s, %s, %s);", (2, stud_permission[0], stud_permission[1], stud_permission[2],))
            conn.commit() # Commit this change to GIT in supabase
            
        print("Initial Permissions Table Created.") 

# Dynamic Tables (i.e. Information inside of it can be updated by the Librarian-Admin during runtime)
# Initially an empty table
def createUsersTable():
    cursor.execute(CREATE_USERS_TABLE)
    conn.commit() 
    print("Initial Users Table Created") 

def createBooksTable():
    cursor.execute(CREATE_BOOKS_TABLE)

    cursor.execute("SELECT COUNT(*) FROM books;")
   
    row_count = cursor.fetchone()[0]
    if row_count == 0:

        with open('booklist.json', 'r') as books_list:
            books_list = json.load(books_list)

        for book_info in books_list:
            book_isbn_id, title, author, published_year, total_book_count, available_count = book_info.values() # Unpack JSON-object
            cursor.execute("INSERT INTO books (book_isbn_id, title, author, published_year, total_book_count, available_count) VALUES(%s, %s, %s, %s, %s, %s);", (book_isbn_id, title, author, published_year, total_book_count, available_count,))

        conn.commit()
        print("Initial Books Table Created") 

def createUserBookCheckoutsTable():
    cursor.execute(CREATE_USER_BOOK_CHECKOUTS_TABLE)
    conn.commit() # Commit to Remote Supbase-Database repo, instead of just my local-db repo...
    print("Initial, Many-To-Many User_To_Borrowed_Books_and_Checkout_Times Table Created; for faster querying && minimal complexity") 

setStaticRolesTable()
setStaticPermissionsTable()

createUsersTable()
createBooksTable()
createUserBookCheckoutsTable()

def hasPermissions(role_id, table_name, action, column_field):
    validate_permission_query = """
                                    SELECT *
                                    FROM permissions
                                    WHERE role_id = %s AND table_name = %s AND action = %s AND column_field = %s
                                """

    cursor.execute(validate_permission_query, (role_id, table_name, action, column_field,))
    res = cursor.fetchone()

    return res != None 

def updateOverdueBooksPerUser(): # just update it for all users, when a single user borrows a book (to save on multi-user api-call costs [1000s of users...])
    update_overdue_books_query = """ 

        -- First: Link foreign key to the table (hence overdue_books.user_id)
        -- 1. With(...)-statement: Select all overdue books (i.e. have a checkout_time >= 1 month from now)
            -- from the user_book_checkouts table
        -- 2. UPDATE users: Now, we align the 'books_overdue' column-field
            -- of users to reflect the overdue-books for each user (foreign-key RELATIONALLY LINKED
            -- by their user_id :) )
        -- 3. SET books_overdue = COALESCE(overdue_books.overdue_books, ARRAY[]::TEXT[]):
            -- If no overdue books are found for that user_id, return []
            -- | i.e.: overdue_books.get(overdue_books, []) [
            -- (i.e.: If this user has no overdue-books, then their 'books_overdue_column'
            -- stays as an EMPTY-ARRAY text[])
        -- 3a. SET books_overdue = means set the returned value to the column_field
            -- 'books_overdue' value, FOR SAID 'user_id' row-entry in users (does so for
            -- all users in the user-table, 1-by-1 via query :) )   

        WITH overdue_books AS (
            SELECT 
                ubc.user_id,
                array_agg(ubc.book_isbn_id) AS overdue_books
            FROM 
                user_book_checkouts ubc -- ubc == alias for 'user_book_checkouts'
            WHERE 
                checkout_time < NOW() - INTERVAL '1 month' -- < 1 month is fine | >= 1 month === overdue
            GROUP BY 
                ubc.user_id
        )
        UPDATE users
        SET books_overdue = COALESCE(overdue_books.overdue_books, ARRAY[]::TEXT[])
        FROM overdue_books
        WHERE users.user_id = overdue_books.user_id;                
    """
    cursor.execute(update_overdue_books_query)
    conn.commit()

updateOverdueBooksPerUser()

@app.get("/api/roles")
def getRoles():
    cursor.execute("SELECT * FROM roles")
    return jsonify({"data": [{"role_id": role_id, "role_name": role_name} for role_id, role_name in cursor.fetchall()]}), 200

@app.get("/api/users/usernames")
def getUserNames():
    cursor.execute("SELECT user_name FROM users")
    usernames_list = [user_name[0] for user_name in cursor.fetchall()]
    return jsonify({"usernames_list": usernames_list}), 200

@app.get("/api/users")
def getUsers():

    updateOverdueBooksPerUser()

    try:

        status = request.args.get("status") # From url-path query params (rq.args.get("...[?status=...]"))
        query = "SELECT * FROM users"

        # url: https://127.0.0.1:5000/api/users?status=excessive-overdue
        if status == "excessive-overdue":
            query += " WHERE array_length(books_overdue, 1) > 3" # 1 represents 1st-dimension of array (i.e. # rows | arrays are stored as ND by default)
        
        # url: https://127.0.0.1:5000/api/users?status=needs-approval
        elif status == "needs-approval":
            query += " WHERE is_active_account=FALSE AND (array_length(books_overdue, 1) IS NULL or array_length(books_overdue, 1) <= 3)"
        
        cursor.execute(query)
        conn.commit()

        column_fields = [desc[0] for desc in cursor.description] # desc[1] = col-field-value for this row-entry 
        filtered_users = cursor.fetchall()
        users = [] # Array of user-json objects
        for user in filtered_users:
            user_details = {}
            for col, user_detail in zip(column_fields, user):
                if col != "password_hash" and col != "id" and col != "string_password_hash":
                    user_details.update({col : user_detail})
            users.append(user_details)

            print(user_details)

        return jsonify({"users": users}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.patch("/api/<user_id>/update-active-status") # user_id is pulled from the query-param-path, hence its in the function-arg directly
def updateActiveStatus(user_id : str):

    request_header_data = request.get_json()

    role_id = request_header_data.get("role_id")
    table_name = request_header_data.get("table_name")
    action = request_header_data.get("action")
    column_field = request_header_data.get("column_field", "N/A")

    activate_account =  request_header_data.get("new_active_status")
    # True = Activate Account
    # False = Deactivate Account
    
    if hasPermissions(role_id, table_name, action, column_field):

        # True or False (activate/deactivate)
        if activate_account != None:
        
            try: 

                cursor.execute("UPDATE users SET is_active_account = %s WHERE user_id = %s", (activate_account, user_id,))
                conn.commit()

                return jsonify({"message": f"User {user_id} active account status updated to {activate_account}"}), 200

            except Exception as e: # Handle database exceptions for caught-errors
                conn.rollback() # Undo the committed SQL-changes for this recent SET OF COMMITS / Transaction Session
                return jsonify({"error": str(e)}), 500
       
        else:
            return jsonify({"error": "Missing 'new_active_status' field in request body"}), 400

    else:
        return jsonify({"error": "You are not permitted to perform this action!"}), 403

@app.post("/api/users")
def processUser(): # Log-in or Create New User-account, depending on if it already exists.
   
    request_header_data = request.get_json()
    
    # Get all data-fields (columns) required to create the user in my table
    role_id = request_header_data.get("role_id")
    user_id = request_header_data.get("user_id") # librarian/student ID # (3 digits vs. 9 digits | validation again in 
    # backend for intercepted, modified requests)
    user_name =  request_header_data.get("user_name")
    password = request_header_data.get("password") # For security, store hash of password (not password explicitly) in my database

    if not user_name or not password or not role_id or not user_id:
        return jsonify({'error': 'All fields are necessary'}), 400
    
    # Invalid Non-NULL Role_ID
    elif not (1 == role_id or 2 == role_id):
        return jsonify({'error': f"Role_id must be either {'1'} or {'2'}"}), 400

    # Librarian ID:
    elif role_id == 1:
        # userID | if not 3 digits + proper regex format for librarians (3 digits) | 9^1 * 10^2 === total librarian-combos
        # Return HTML-message error
        id_pattern = r'^\d{4}$' # 4 digits == librarianID
        if not re.match(id_pattern, user_id):
            print("here 3")
            return jsonify({"error": f"""Librarian {'userID'} must be exactly 4 digits."""}), 400

    # Student ID:
    elif role_id == 2:
        # userID | if not (9 digits) + proper regex format for students + proper regex format for students
        # Return HTML-message error
        id_pattern = r'^\d{9}$' # 9 digits == studentID
        if not re.match(id_pattern, user_id):
            print("here 4")
            return jsonify({"error": f"""Student {'userID'} must be exactly 9 digits."""}), 400

    try: 

        # Check if this user already exists — if so, return 'Welcome Back' (account already exists),
        # instead of duplicating the entry in the table
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user_exists = cursor.fetchone() 

        # * FIRST: Check If this user already exists (to avoid unnecessary computations if the user doesn't) [i.e., as below]
        if user_exists:

            # * Get/Fetch password-hash (password CIPHERTEXT w/ un-enc salt sprinkled on top)
            # * for this existing user_account
            cursor.execute("SELECT password_hash FROM users WHERE user_id = %s", (user_id,))
            stored_password_hash = cursor.fetchone()[0] # Tuple of 1 element/column_field | * === tuple of all column_fields for this entry
            stored_password_hash = bytes(stored_password_hash) # Convert from memory-view format back to bytes-format :)

            correct_password = (stored_password_hash == bcrypt.hashpw(password.encode('utf-8'), stored_password_hash))
            if correct_password:
                is_active_account = user_exists[5] # Get Active Status, i.e. 5th element in returned tuple of row-entry values (i.e. column_field values)
                if not is_active_account:
                    num_books_overdue = len(user_exists[6])
                    if num_books_overdue == 0: # New account
                        return jsonify({'error': 'A librarian will activate your newly created account shortly.'}), 403
                    
                    return jsonify({'error': """You're account has been deactivated for >3 overdue books. Please return them to access your account."""}), 403
                
                cursor.execute("SELECT * FROM user_book_checkouts WHERE user_id = %s", (user_id,))
                book_checkouts = [book_isbn_id for x, book_isbn_id, z in cursor.fetchall()]
                return jsonify({'message': 'Welcome Back!', 'user_id': user_id, 'is_active_account': is_active_account, 'book_checkouts': book_checkouts}), 201  # Log-in Success 
            else:
                return jsonify({'error': 'Invalid Password. Please Try Again!'}), 401  # Log-in Attempt #1 | Try Again

        else:
            cursor.execute("SELECT * FROM users WHERE user_name = %s", (user_name,))
            is_duplicate_user_name = cursor.fetchone()
            if is_duplicate_user_name:
                print("here 7")
                return jsonify({'error': 'Username is taken! Please enter a new username.'}), 409 # Error
        
        # Random salt to prevent rainbow-table attacks,
        # which map/backtrack common passwords from their STATIC encrypted-text (cipher-text)
        random_salt = bcrypt.gensalt()
        
        # Generate cipher-text, w/ unique salt sprinkled on top for randomness...
        password_hash = bcrypt.hashpw(password.encode('utf-8'), random_salt)

        # Insert new-user entry into my database
        # -- non-serial, non-default values are explicitly inserted
        cursor.execute(
            """
                INSERT INTO users (role_id, user_id, user_name, password_hash, is_active_account, books_overdue, string_password_hash)
                VALUES ( 
                    %s, %s, %s, %s, %s, %s, %s
                );
            """,
            (role_id, user_id, user_name, password_hash, 'TRUE' if role_id == 1 else 'FALSE', [], password_hash)       
        )
        conn.commit()

        return jsonify({'message': 'Congratulations! You have made an account!', 'user_id': user_id, 'is_active_account': False}), 200  # Sign-Up-Creation-Success Success 

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.get("/api/books")
def getBooks():

    # Update the # of overdue books (check time-diff b/w checkout_time && NOW() >= 1 month) for each user
    updateOverdueBooksPerUser()

    request_url_query_param_data = request.args
    role_id = int(request_url_query_param_data.get("role_id")) # Convert back from string (url-query-param) to integer
    table_name = request_url_query_param_data.get("table_name")
    action = request_url_query_param_data.get("action")
    column_field = request_url_query_param_data.get("column_field", "N/A")

    if hasPermissions(role_id, table_name, action, column_field):
        cursor.execute(f"""{action} {column_field} FROM {table_name};""") # Tuple of each column-value | 'rows' (r) tuples total
        res = cursor.fetchall() # Get ALL books, i.e. ALL row-entries in the books-table
        books = [OrderedDict({"book_isbn_id": book_isbn_id, "title": title, "author": author, "published_year": published_year, "total_book_count": book_count, "available_count": available_count}) for book_isbn_id, title, author, published_year, book_count, available_count in res]
        return jsonify({"books": books}), 200

    # Invalid Role_ID 
    else:
        return jsonify({"error": "You are not permitted to view this resource!"}), 403


@app.post("/api/books")
def insertBook():

    request_header_data = request.get_json()

    role_id = request_header_data.get("role_id")
    table_name = request_header_data.get("table_name")
    action = request_header_data.get("action")
    column_field = request_header_data.get("column_field", "N/A") # 'None' for Insert/Delete queries (queries for ENTIRE ROW-ENTRIES -> NOT just a specific column to only work on)

    book_isbn_id = request.get_json("book_isbn_id")
    title = request.get_json("title")
    author = request.get_json("author")
    published_year = request.get_json("published_year")
    total_book_count = request.get_json("total_book_count")
    available_count = request.get_json("available_count")

    # Validate missing fields
    if not book_isbn_id or not title or not author or not published_year or not total_book_count or not available_count:
        return jsonify({'error': 'All fields are necessary'}), 400

    # Check for duplicate books
    cursor.execute("SELECT * FROM books WHERE book_isbn_id = %s", (book_isbn_id,)) # Ensure you pass a single-element tuple for book_isbn_id. In Python, a single-element tuple requires a trailing comma (i.e., (book_isbn_id,))
    book = cursor.fetchone() # Unique Books in table only, so fetchone() works (no need for fetchall()[0]-tuple)
    if book: # book == None => New book-entry in 'books_table' :)
        return jsonify({'error': 'Book {book_isbn_id} already exists!'}), 400

    if hasPermissions(role_id, table_name, action, column_field):
        try: 

            cursor.execute("INSERT into books (book_isbn_id, title, author, published_year, total_book_count, available_count) VALUES (%s, %s, %s, %s, %s, %s, %s);", (book_isbn_id, title, author, published_year, total_book_count, available_count,))
            conn.commit()

            return {"message": f"New book {book_isbn_id} added."}, 200
        
        except Exception as e: # Handle database exceptions
            conn.rollback() 
            return jsonify({"error": str(e)}), 500 # Database-logic error (NOT a user error) -> HTTP-error-status code '500'
    
    else:
        return jsonify({"error": "You are not permitted to perform this action!"}), 403


@app.delete("/api/books/<book_isbn_id>") # book_isbn_id is pulled from the query-param-path, hence its in the function-arg directly
def removeBook(book_isbn_id : str):

    request_header_data = request.get_json()

    role_id = request_header_data.get("role_id")
    table_name = request_header_data.get("table_name")
    action = request_header_data.get("action")
    column_field = request_header_data.get("column_field", "N/A") # 'None' for Insert/Delete queries (queries for ENTIRE ROW-ENTRIES -> NOT just a specific column to only work on)

    # Will only run the below code if these 4 params insert within the exact same row-entry
    # in my permissions-table — SO, by default, a SQL-injection won't push through here.
    if hasPermissions(role_id, table_name, action, column_field):
        try: 

            # NOTE: First, check if students currently borrowing this book (can't remove it from the system
            # until ALL COPIES are returned back)
            cursor.execute('SELECT * FROM user_book_checkouts where book_isbn_id = CAST(%s AS TEXT);', (str(book_isbn_id),))
            if cursor.rowcount != 0:
                return jsonify({"error": "Students are currently borrowing this book!"}), 409


            cursor.execute("DELETE FROM books WHERE book_isbn_id=0060597720;")
            if cursor.rowcount == 0:
                return {"message": f"No matching book found. Nothing deleted."}, 404 # 404 not found
            
            conn.commit() # MAKE SURE TO COMMIT THESE CHANGES TO SUPABASE (i.e. remote-repo),
            # SO I CAN ACTUALLY SEE THEM (i.e. not just reflected in my local database)

            return {"message": f"Book {book_isbn_id} deleted."}, 200
        
        except Exception as e: # Handle database exceptions
            return jsonify({"error": str(e)}), 500
    
    else:
        return jsonify({"error": "You are not permitted to perform this action!"}), 403

@app.patch("/api/books/<book_isbn_id>") 
def updateBookInfo(book_isbn_id : str):

    request_header_data = request.get_json()

    role_id = request_header_data.get("role_id")
    table_name = request_header_data.get("table_name")
    action = request_header_data.get("action")
    column_field = request_header_data.get("column_field", "N/A") # 'None' for Insert/Delete queries (queries for ENTIRE ROW-ENTRIES -> NOT just a specific column to only work on)

    valid_updatable_book_headers = set({"book_isbn_id", "title", "author", "published_year", "total_book_count", "available_count"})

    set_clause = [] 
    defined_param_values_to_replace = []

    new_book_isbn_id = book_isbn_id

    # for curr_val, val_to_replace_with
    for old_val, new_val in request_header_data.items():
        if old_val in valid_updatable_book_headers and new_val != None: 

            set_clause.append(f'{old_val} = %s')
            defined_param_values_to_replace.append(new_val)

            if old_val == "book_isbn_id": # New book_isbn_id provided | Changed (hence in json-headers)
                new_book_isbn_id = new_val
    
    # If no valid fields were provided
    if not set_clause:
        # If no valid fields were provided
        return jsonify({"error": "No valid fields provided for update"}), 400
    
    set_clause = (", ").join(set_clause)
    query = f"""UPDATE books
                SET {set_clause}
                WHERE book_isbn_id = %s"""
    
    # Change to tuple (that's what the cursor.execute accepts for the parameterized-queries | immutable)
    defined_param_values_to_replace.append(book_isbn_id) # Old 'book_isbn_id' is also a parameterized-query %s (to select which book-row-entry to search for)
    defined_param_values_to_replace_tuple = tuple(defined_param_values_to_replace)

    # Will only run the below code if these 4 params insert within the exact same row-entry
    # in my permissions-table — SO, by default, a SQL-injection won't push through here.
    if hasPermissions(role_id, table_name, action, column_field):
        try: 
            cursor.execute(query, defined_param_values_to_replace_tuple)
            conn.commit()

            cursor.execute("SELECT * from books where book_isbn_id = %s", (new_book_isbn_id,))
            column_fields = [desc[0] for desc in cursor.description] # desc[1] = col-field-value for this row-entry 
    
            updated_book_values = cursor.fetchone()
            book_info = dict(zip(column_fields, updated_book_values))
            book_info = json.dumps(book_info)

            return {"message": f"Book {new_book_isbn_id} succesfully updated.",
                    "updated_book" : book_info
                   }, 200
        
        except Exception as e: # Handle database exceptions
            conn.rollback() 
            return jsonify({"error": str(e)}), 500
    
    else:
        return jsonify({"error": "You are not permitted to perform this action!"}), 403

@app.patch("/api/users/<user_id>/borrow-book") # user_id is pulled from the query-param-path, hence its in the function-arg directly
def borrowBook(user_id : str):

    # First update the overdue-books for this user_id | update their books_overdue column accordingly
    updateOverdueBooksPerUser()

    # Then: Check if the updated overdue-books count for this user_id
    # is now EXCESSIVELY OVERDUE
    cursor.execute("SELECT books_overdue FROM users where user_id = %s AND array_length(books_overdue, 1) > 3", (user_id,))
    if cursor.fetchone(): 
        return jsonify({"error": "You have exceeded the overdue-limit. Please return your overdue books to continue borrowing books."}), 403 # 403 Forbidden | Valid Request from AUTHENTICATED CLIENT; BUT: They are restricted from borrowing books b/c of the >3 overdue books-policy violation...

    # USER CAN'T BORROW A BOOK (deactivated_account) "You're account is currently deactivated. You either have >3 overdue books OR are a newly registered user (wait for librarian approval)."
    cursor.execute("SELECT is_active_account FROM users WHERE user_id = %s", (user_id,))
    is_active = cursor.fetchone()[0]
    if not is_active: # deactivated account
        return jsonify({"error": "You're account is currently deactivated. You either have >3 overdue books OR are a newly registered user (wait for librarian approval)."}), 403 # Forbidden

    # JSON-header-fields specified for MOST FRONTEND API-REQUESTS :)
    # + additional elements as below (i.e. book_isbn_id)
    request_header_data = request.get_json()

    role_id = request_header_data.get("role_id")
    table_name = request_header_data.get("table_name")
    action = request_header_data.get("action")
    column_field = request_header_data.get("column_field", "N/A")

    book_isbn_id = request_header_data.get("book_isbn_id")
    
    if hasPermissions(role_id, table_name, action, column_field):
        
        try: 
            cursor.execute("SELECT available_count FROM books WHERE book_isbn_id = %s", (book_isbn_id,))
            books_available_count = cursor.fetchone()

            # books_available_count == None -> Empty Return Value | -> provided books_isbn_id doesn't exist in the Books_table :)
            if not books_available_count or books_available_count[0] == 0:
                return {"error": "Book not available"}, 400
            
            cursor.execute(f"""{action} INTO {table_name} (user_id, book_isbn_id, checkout_time) VALUES (%s, %s, NOW());""", (user_id, book_isbn_id,))
            
            # Update 'books_checked_out' to DECREMENT by 1 for this user_id field
            # cursor.execute("UPDATE books SET books_available_count = books_available_count - 1 WHERE book_isbn_id = %s", (book_isbn_id,))
            cursor.execute(f"""UPDATE books
                SET available_count = available_count - 1
                WHERE book_isbn_id = {book_isbn_id}""")
            
            conn.commit()

            return {"message": "Book checked out succesfully!"}, 200
        
        except Exception as e: # Handle database exceptions for caught-errors
            conn.rollback() 
            return jsonify({"error": "Unable to borrow book", "details": str(e)}), 500
    
    else:
        return jsonify({"error": "You are not permitted to perform this action!"}), 403
    
@app.patch("/api/users/<user_id>/return-book") # user_id is pulled from the query-param-path, hence its in the function-arg directly
def returnBook(user_id : str):

    updateOverdueBooksPerUser()

    request_header_data = request.get_json()

    role_id = request_header_data.get("role_id")
    table_name = request_header_data.get("table_name")
    action = request_header_data.get("action")
    column_field = request_header_data.get("column_field", "N/A")

    book_isbn_id = request_header_data.get("book_isbn_id")
    
    if hasPermissions(role_id, table_name, action, column_field):
        
        try: 
            cursor.execute("SELECT * FROM books WHERE book_isbn_id = %s", (book_isbn_id,))
            book = cursor.fetchone()

            # book == None -> Empty Return Value | -> provided books_isbn_id doesn't exist in the Books_table :)
            if not book:
                return {"error": "Book not found"}, 400
            
            # "DELETE FROM user_book_checkouts WHERE user_id = user_id AND book_isbn_id = book_isbn_id
            cursor.execute(f"""{action} FROM {table_name} 
                            WHERE user_id = %s AND book_isbn_id = %s;""", 
                            (user_id, book_isbn_id,))
            
            cursor.execute(f"""UPDATE books
                SET available_count = available_count + 1
                WHERE book_isbn_id = {book_isbn_id}""")
            
            conn.commit()

            return {"message": "Book returned successfully!"}, 200
        
        except Exception as e: # Handle database exceptions for caught-errors              
            conn.rollback() 
            return jsonify({"error": "Unable to return book", "details": str(e)}), 500
    
    else:
        return jsonify({"error": "You are not permitted to perform this action!"}), 403