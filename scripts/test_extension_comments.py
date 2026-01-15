"""
Test file to trigger inline comments for extension testing.
This file contains intentional issues that should generate comments.
"""

import os
import subprocess


def process_user_data(user_id, items=[]):
    """
    Process user data - has mutable default argument issue.
    Python analyzer should flag this.
    """
    for item in items:
        items.append(item * 2)
    return items


def fetch_api_data(endpoint):
    """
    Fetch data from API - has bare except and print statement.
    """
    try:
        response = {"data": "test", "status": 200}
        print(f"Fetched data from {endpoint}")
        return response
    except:
        print("Error fetching data")
        return None


def get_database_config():
    """
    Get database configuration - has hardcoded credentials.
    Security analyzer should flag this.
    """
    db_password = "super_secret_password_123"
    api_key = "sk-1234567890abcdefghijklmnop"
    
    return {
        "host": "localhost",
        "port": 5432,
        "password": db_password,
        "api_key": api_key,
    }


def calculate_totals(orders):
    """
    Calculate order totals - uses mutation instead of reduce.
    Could be improved with functional approach.
    """
    total = 0
    count = 0
    for order in orders:
        total = total + order.get("amount", 0)
        count = count + 1
    
    print(f"Processed {count} orders, total: {total}")
    return {"total": total, "count": count}


def run_shell_command(user_input):
    """
    Run a shell command - potential command injection.
    Security analyzer should flag this.
    """
    command = f"ls -la {user_input}"
    result = subprocess.run(command, shell=True, capture_output=True)
    return result.stdout.decode()


class UserService:
    """Simple user service with some issues."""
    
    def __init__(self):
        self.users = []
        self.api_token = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    
    def add_user(self, user):
        """Add a user to the list."""
        self.users.append(user)
        print(f"Added user: {user}")
    
    def get_user_by_id(self, user_id):
        """Get user by ID with bare except."""
        try:
            for user in self.users:
                if user.get("id") == user_id:
                    return user
            return None
        except:
            return None
    
    def process_all_users(self, callback):
        """Process all users."""
        results = []
        for user in self.users:
            result = callback(user)
            results.append(result)
            print(f"Processed user {user.get('id')}")
        return results


if __name__ == "__main__":
    service = UserService()
    service.add_user({"id": 1, "name": "Test User"})
    
    config = get_database_config()
    print(f"Config loaded: {config}")
    
    data = fetch_api_data("/api/users")
    print(f"API data: {data}")
    
    orders = [{"amount": 100}, {"amount": 200}, {"amount": 50}]
    totals = calculate_totals(orders)
    print(f"Totals: {totals}")
