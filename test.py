from dotenv import load_dotenv
import os
import psycopg2

def test_database_connection():
    """Tests the database connection using the DATABASE_URL from environment variables.
    Outputs the connection status to the console.
    """
    # Load environment variables from .env file to access database connection details
    load_dotenv()


    # Retrieve the database URL from the loaded environment variables
    database_url = os.getenv("DATABASE_URL")
    print(database_url)
    #database_url="postgresql://postgres:nadia123@LOCALHOST:5445/ExpenseTracker"
    if database_url:
        try:
            # Establish a connection to the database
            conn = psycopg2.connect(database_url)
            print("Connection to the database successful!")

            # Close the connection
            conn.close()

        except psycopg2.OperationalError as e:
            print(f"Connection failed! Error: {e}")
    else:
        print("DATABASE_URL not found in the .env file")

if __name__ == "__main__":
    test_database_connection()
