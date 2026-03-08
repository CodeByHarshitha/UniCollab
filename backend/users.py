import csv
from models import User, ProfileData
import os

# In-memory storage for users and projects
users_db = {}
projects_db = []

def load_test_users():
    csv_path = os.path.join(os.path.dirname(__file__), "test_users.csv")
    if not os.path.exists(csv_path):
        return
        
    with open(csv_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            email = row['email'].strip()
            users_db[email] = {
                "password": row['password'].strip(),
                "user": User(email=email, name=row['name'].strip())
            }
