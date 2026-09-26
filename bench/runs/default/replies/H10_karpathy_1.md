```python
def notify_all(users, message):
    for i in range(1, len(users)):
        user = users[i]
        if user.active:
            user.send(message)
```

**Possible bug (unchanged):** `range(1, len(users))` starts at index 1, so the first user is never notified. If that's unintended, the fix would be:

```python
for user in users:
    if user.active:
        user.send(message)
```

Want me to apply that?
