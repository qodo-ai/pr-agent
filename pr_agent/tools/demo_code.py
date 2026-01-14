"""Demo file to trigger Python analyzer."""

def demo_function():
    print("This WILL trigger an analyzer warning!")
    data = []
    for i in range(10):
        data.append(i)
    return data
