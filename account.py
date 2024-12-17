import mysql.connector

class AccountManager:
    """
    Initialize the account manager with a database connection
    """
    def __init__(self, db):
        self.db = db

    """
    User login
    """
    def login(self, username, password):
        print(f"Attempting login with username: {username} and password: {password}")

        # Connect to the specific database based on the username
        self.db.connect(username)  # Determine the server to connect to based on the username

        if not self.db.connection:
            print(f"Failed to connect to database for user: {username}")
            return None

        try:
            # Adjust the query based on the actual column names in the database
            query = "SELECT * FROM users WHERE username = %s AND password_hash = %s"
            cursor = self.db.connection.cursor()
            cursor.execute(query, (username, password))

            # Get the user data
            user = cursor.fetchone()  # Return the complete user information
            cursor.close()

            print(f"User found: {user}")

            # Check if the user exists
            if user:
                print(f"User {username} logged in successfully!")
                return user
            else:
                print(f"Invalid username or password for {username}")
                return None

        except mysql.connector.Error as e:
            print(f"Database error during login for user {username}: {e}")
            return None