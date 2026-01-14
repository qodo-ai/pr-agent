"""Test file to trigger Python analyzer."""

def test_function():
    print("This should trigger an analyzer warning!")
    data = []
    for i in range(10):
        data.append(i)
    return data
