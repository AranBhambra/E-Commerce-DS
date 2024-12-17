import mysql.connector
from mysql.connector import Error
import hashlib

# Database class to handle database connection

class Database:
    """
    Initialize the database connection object
    """
    def __init__(self, server=None):
        """
        Specify server identifier (A, B, or C) at initialization to connect to the respective database
        """
        self.connection = None
        self.server = server

    """
    Map a username to a specific server
    """
    def get_server_from_username(self, username):

        # Using the hash value of the username to determine the server
        if not self.server:
            hash_value = int(hashlib.sha256(username.encode()).hexdigest(), 16)
            server_number = hash_value % 3  # Assume there are 3 servers

            if server_number == 0:
                self.server = "A"
            elif server_number == 1:
                self.server = "B"
            else:
                self.server = "C"
        
            print(f"User '{username}' is assigned to server {self.server}")
        return self.server

    """
    Connect to the specific database based on the username
    """
    def connect(self, username=None):
        # Get the server corresponding to the username
        if username:
            self.get_server_from_username(username)

        try:
            print(f"Attempting to connect to the database on server {self.server}...")
            
            # Connect to the respective database based on the server identifier
            if self.server == "A":
                self.connection = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password="toronto@2024",
                    database="e_store_a"
                )
            elif self.server == "B":
                self.connection = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password="toronto@2024",
                    database="e_store_b"
                )
            elif self.server == "C":
                self.connection = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password="toronto@2024",
                    database="e_store_c"
                )
            else:
                raise ValueError("Invalid server identifier. Please specify 'A', 'B', or 'C'.")

            # Check if the connection is successful
            if self.connection.is_connected():
                print("Database connected successfully.")

                # Test the connection to ensure it is working
                cursor = self.connection.cursor()
                cursor.execute("SELECT DATABASE();")
                result = cursor.fetchone()
                print(f"Connected to database: {result[0]}")
                cursor.close()

        except Error as e:
            print(f"Failed to connect to database on server {self.server}: {e}")
            self.connection = None


    """
    Close the database connection
    """
    def close(self):
        if self.connection:
            self.connection.close()
            print("Database connection closed.")
