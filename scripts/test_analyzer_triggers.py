"""
Test file to trigger static analyzer findings and AI suggestions.
This file intentionally contains code issues for testing PR Agent inline comments.
"""

import os
import pickle


def process_user_data(users=[]):
    """Function with mutable default argument - should trigger B006."""
    for user in users:
        print(f"Processing: {user}")
    return users


def unsafe_deserialize(data):
    """Using pickle for deserialization - security risk S301."""
    return pickle.loads(data)


def connect_to_database():
    """Hardcoded credentials - should trigger security analyzer."""
    db_password = "super_secret_password_123"
    api_key = "sk-1234567890abcdef"
    
    connection_string = f"postgresql://admin:{db_password}@localhost:5432/prod"
    return connection_string


def calculate_discount(price, discount_type):
    """Complex nested conditionals - AI should suggest simplification."""
    if discount_type == "premium":
        if price > 100:
            if price > 500:
                return price * 0.7
            else:
                return price * 0.8
        else:
            return price * 0.9
    elif discount_type == "standard":
        if price > 100:
            return price * 0.85
        else:
            return price * 0.95
    else:
        return price


def fetch_data(url):
    """Bare except clause - should trigger E722."""
    try:
        response = os.system(f"curl {url}")
        return response
    except:
        print("Something went wrong")
        return None


def process_items(items):
    """Inefficient loop pattern - AI should suggest list comprehension."""
    result = []
    for item in items:
        if item > 0:
            result.append(item * 2)
    return result


class UserService:
    """Service class with some issues."""
    
    def __init__(self):
        self.secret_token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    
    def validate_input(self, data):
        """No input validation - security concern."""
        return eval(data)
    
    def log_action(self, action, user_id):
        """Using print instead of proper logging."""
        print(f"User {user_id} performed {action}")


def main():
    """Main function to test the code."""
    service = UserService()
    
    users = process_user_data()
    users.append({"name": "test"})
    
    discount = calculate_discount(150, "premium")
    print(f"Final price: {discount}")
    
    data = fetch_data("http://example.com/api")
    
    numbers = [1, -2, 3, -4, 5]
    processed = process_items(numbers)
    print(f"Processed: {processed}")


if __name__ == "__main__":
    main()
