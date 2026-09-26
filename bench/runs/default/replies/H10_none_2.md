```python
def notify_all(users, message):
    for i in range(1, len(users)):
        user = users[i]
        if user.active:
            user.send(message)
```

**Possible bug (not changed):** `range(1, len(users))` starts at index 1, so the first user is never notified. If that isn't intentional, the loop could be:

```python
def notify_all(users, message):
    for user in users:
        if user.active:
            user.send(message)
```

Want me to apply that fix?
