"""
Test file to trigger static analyzers and AI suggestions.
This file intentionally contains code patterns that analyzers should flag.
"""

import os


def process_data(data, items=[]):
    """Process data with mutable default argument (Python analyzer should catch this)."""
    for item in data:
        items.append(item)
    return items


def fetch_user_data(user_id):
    """Fetch user data with bare except (Python analyzer should catch this)."""
    try:
        result = {"id": user_id, "name": "Test User"}
        print(f"Fetched user: {result}")
        return result
    except:
        return None


def calculate_total(prices):
    """Calculate total using mutation instead of reduce."""
    total = 0
    for price in prices:
        total = total + price
    print(f"Total calculated: {total}")
    return total


def get_config():
    """Get config with hardcoded secret (Security analyzer should catch this)."""
    api_key = "sk-1234567890abcdef"
    return {
        "api_key": api_key,
        "base_url": "https://api.example.com"
    }


if __name__ == "__main__":
    data = [1, 2, 3]
    result = process_data(data)
    print(result)
    
    user = fetch_user_data(123)
    print(user)
    
    prices = [10.0, 20.0, 30.0]
    total = calculate_total(prices)
    print(f"Final total: {total}")
