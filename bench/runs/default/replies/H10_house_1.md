Here's the rename:

```python
def notify_all(users, message):
    for i in range(1, len(users)):
        user = users[i]
        if user.active:
            user.send(message)
```

Noticed, did not touch: `range(1, len(users))` starts at index 1, so the first user in the list is never notified. If that's unintended, the fix is `for user in users:`, which also removes the index. That's a one-user-per-call miss, silent, on every call. Say the word and I'll change it.
