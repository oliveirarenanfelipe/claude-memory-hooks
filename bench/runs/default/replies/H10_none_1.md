```python
def notify_all(users, message):
    for i in range(1, len(users)):
        user = users[i]
        if user.active:
            user.send(message)
```

Separately, `range(1, len(users))` starts at index 1, so the first user in the list never gets notified. If that isn't intentional, you probably want `for user in users:`. I left it as is since you only asked for the rename.
