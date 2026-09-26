```python
def notify_all(users, message):
    for i in range(1, len(users)):
        user = users[i]
        if user.active:
            user.send(message)
```

I left one thing unchanged that you may want to check. `range(1, len(users))` starts at index 1, so the first user in the list never gets notified. If that's not intentional, the fix would be:

```python
def notify_all(users, message):
    for user in users:
        if user.active:
            user.send(message)
```
