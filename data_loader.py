import pandas as pd
from pymongo import MongoClient

def load_data_from_mongodb():
    """
    Connects to MongoDB Atlas using provided credentials and fetches data from the `key_task` database.
    Returns three DataFrames: clients, memberships, transactions.
    """
    # MongoDB connection details
    MONGO_URI = "mongodb+srv://nampardrakpa:wEQrlZQLRcbkF8cA@cluster0.rho0b.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    DB_NAME = "key_task"

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
