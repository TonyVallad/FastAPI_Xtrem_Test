# DateTime and Timezone Handling

## Best Practices

The FastAPI_Xtrem_Test application follows these best practices for handling dates and times:

1. **Always store timestamps in UTC**: All timestamps in the database are stored in UTC format. This provides a consistent, unambiguous reference point regardless of where users or servers are located.

2. **Use timezone-aware datetime objects**: All datetime objects should include timezone information, especially when performing comparisons or operations between different datetime values.

3. **Convert to UTC for storage**: Even if a timestamp is initially created with a different timezone, it should be converted to UTC before being stored in the database.

4. **Ensure timezone information when comparing dates**: When comparing two datetime objects, both must have timezone information to avoid the `TypeError: can't compare offset-naive and offset-aware datetimes` error.

## Implementation Details

### Core Utilities

The application provides a utility function in `api/auth/security.py` to ensure datetime objects have timezone information:

```python
def ensure_timezone(dt):
    """Ensure a datetime object has timezone information"""
    if dt and not dt.tzinfo:
        return dt.replace(tzinfo=timezone.utc)
    return dt
```

### Creating Timestamps

When creating timestamps, always use the timezone-aware version:

```python
# Correct:
from datetime import datetime, timezone
current_time = datetime.now(timezone.utc)

# Incorrect (avoid):
current_time = datetime.utcnow()  # This is deprecated and timezone-naive
```

### Comparing Timestamps

When comparing timestamps, ensure both have timezone information:

```python
# Correct:
if ensure_timezone(timestamp1) < ensure_timezone(timestamp2):
    # Do something

# Or with explicit null checks:
if timestamp1 and timestamp2 and ensure_timezone(timestamp1) < ensure_timezone(timestamp2):
    # Do something
```

### Handling Refresh Tokens

Refresh tokens store an expiration timestamp. When validating a token:

1. Fetch the token from the database
2. Ensure the token's expiration timestamp has timezone information
3. Compare against the current UTC time

```python
# Example from api/users/routes.py
current_time = datetime.now(timezone.utc)
    
# Ensure expires_at has timezone information
if db_token.expires_at:
    db_token.expires_at = ensure_timezone(db_token.expires_at)
    db.commit()
    db.refresh(db_token)

# Ensure explicit timezone check
token_expires_at = ensure_timezone(db_token.expires_at) if db_token.expires_at else None

if db_token.revoked or (token_expires_at and token_expires_at < current_time):
    # Token is revoked or expired
```

## Testing Considerations

When testing timestamp functionality:

1. Create explicit timezone-aware timestamps in test fixtures
2. Use the `fix_token_timezone` function in tests to ensure database objects have correct timezone information
3. Avoid comparing naive and aware datetime objects

Example from `api/tests/test_token_rotation.py`:

```python
def fix_token_timezone(db: Session, token_string: str):
    """Fix timezone information for token in database"""
    token = db.query(RefreshToken).filter(RefreshToken.token == token_string).first()
    if token:
        # Add timezone info to expires_at if missing
        if token.expires_at:
            token.expires_at = ensure_timezone(token.expires_at)
            
        # Add timezone info to created_at if missing
        if token.created_at:
            token.created_at = ensure_timezone(token.created_at)
            
        # Add timezone info to revoked_at if missing
        if token.revoked_at:
            token.revoked_at = ensure_timezone(token.revoked_at)
            
        db.commit()
        db.refresh(token)
    return token
```

## Common Issues and Solutions

1. **TypeError: can't compare offset-naive and offset-aware datetimes**
   - Solution: Ensure both datetime objects have timezone information before comparison using the `ensure_timezone` function.

2. **Inconsistent datetime formats in database**
   - Solution: Use the `Column(DateTime(timezone=True))` parameter in SQLAlchemy models to ensure all datetime columns store timezone information.

3. **Timezone inconsistency across different environments**
   - Solution: Always use UTC for server operations, and convert to local time only for display purposes in the frontend.

## References

- [Python datetime documentation](https://docs.python.org/3/library/datetime.html)
- [SQLAlchemy DateTime handling](https://docs.sqlalchemy.org/en/14/core/type_basics.html#sqlalchemy.types.DateTime)
- [FastAPI documentation on datetime](https://fastapi.tiangolo.com/tutorial/extra-data-types/) 