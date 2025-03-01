import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
import os

def load_data_from_mongodb():
    """
    Connects to MongoDB Atlas using provided credentials and fetches data from the `key_task` database.
    Returns three DataFrames: clients, memberships, transactions.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Retrieve MongoDB credentials from environment variables
    MONGO_URI = os.getenv("MONGO_URI")
    DB_NAME = os.getenv("DB_NAME")

    if not MONGO_URI or not DB_NAME:
        raise ValueError("MongoDB URI or database name is missing in environment variables.")

    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]

        # Fetch collections
        clients = pd.DataFrame(list(db.clients.find()))
        memberships = pd.DataFrame(list(db.memberships.find()))
        transactions = pd.DataFrame(list(db.transactions.find()))

        # Close the connection
        client.close()

        return clients, memberships, transactions

    except Exception as e:
        raise ConnectionError(f"Failed to connect to MongoDB: {str(e)}")
