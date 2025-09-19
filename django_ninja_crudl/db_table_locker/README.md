# db-table-locker

`db-table-locker` is a simple solution that provides database-agnostic decorator/context-manager to lock database table(s) for a transaction. This is useful when you want to ensure that no other transaction can modify the table(s) while you are performing operations on them, especially in a high-concurrency environment.

## Usage

```python
from django.contrib.auth.models import User
from django.db import transaction
from django_ninja_crudl.db_table_locker.locker import DatabaseTableLocker
from django_ninja_crudl.db_table_locker.context_manager import atomic_lock_tables, lock_tables
from django_ninja_crudl.db_table_locker.decorator import require_atomic_lock_tables

# Example 1: Using context manager with explicit transaction
try:
    with (
        transaction.atomic(),
        lock_tables(User, lock_mode=DatabaseTableLocker.LOCK_EXCLUSIVE),
    ):
        # Perform operations on User table
        user_count = User.objects.count()
        print(f"User count: {user_count}")
except Exception as e:
    print(f"Error: {e}")

# Example 2: Using atomic_table_lock convenience method
try:
    with atomic_lock_tables([User], lock_mode=DatabaseTableLocker.LOCK_SHARE):
        # Read operations with shared lock
        users = list(User.objects.all()[:10])
        print(f"Retrieved {len(users)} users")
except Exception as e:
    print(f"Error: {e}")


# Example 3: Using decorator
@require_atomic_lock_tables(User)
def create_user_safely(username):
    """Create user with table locked to prevent race conditions."""
    if not User.objects.filter(username=username).exists():
        return User.objects.create_user(username=username)
    return None


# Example 4: Multiple tables
try:
    with atomic_lock_tables(["auth_user", "auth_group"]):
        # Work with multiple tables locked
        pass
except Exception as e:
    print(f"Error: {e}")
```
