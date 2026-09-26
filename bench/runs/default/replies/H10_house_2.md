Here's the rename:

```python
def notify_all(users, message):
    for i in range(1, len(users)):
        user = users[i]
        if user.active:
            user.send(message)
```

Noticed, did not touch: `range(1, len(users))` starts at index 1, so the first user in the list is never notified. This looks like an off-by-one bug. If it isn't intentional, `for user in users:` would fix it and remove the index entirely. I haven't verified how callers build `users`, so it's possible skipping the first element is deliberate (e.g., a header or sender at index 0).
