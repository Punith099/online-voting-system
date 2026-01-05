"""
Authentication utilities for JWT tokens and password hashing.

Security concepts explained:
1. Password Hashing: Never store passwords in plain text
   - Uses bcrypt (slow by design to prevent brute-force)
   - Each hash is unique even for same password (due to salt)
   
2. JWT (JSON Web Tokens): Stateless authentication
   - Token contains user info (user_id, role)
   - Signed with secret key (can't be tampered with)
   - Has expiration time (24 hours in this app)
   - Frontend stores in localStorage and sends with each request
"""

from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional, Dict

# Password hashing configuration
# bcrypt is cryptographically secure and slow (prevents brute-force attacks)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
# SECURITY WARNING: In production, use environment variable for SECRET_KEY
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY = "your-secret-key-change-in-production-use-env-variable-123456"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Process:
    1. Generates random salt
    2. Combines password + salt
    3. Runs through bcrypt algorithm (multiple rounds)
    4. Returns hash string (includes salt)
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password (safe to store in database)
    
    Example:
        >>> hash_password("mypassword123")
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7y8cZJ7AkG'
        
    Note: Same password produces different hash each time (due to random salt)
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Process:
    1. Extracts salt from stored hash
    2. Hashes plain_password with same salt
    3. Compares hashes in constant time (prevents timing attacks)
    
    Args:
        plain_password: Password entered by user
        hashed_password: Hash stored in database
    
    Returns:
        True if password matches, False otherwise
    
    Example:
        >>> hashed = hash_password("secret123")
        >>> verify_password("secret123", hashed)
        True
        >>> verify_password("wrong", hashed)
        False
    
    Security:
        Uses constant-time comparison to prevent timing attacks
        (attacker can't determine correct characters by timing)
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict) -> str:
    """
    Create a JWT access token.
    
    Token structure:
    {
        "user_id": "abc123",
        "role": "student",
        "exp": 1234567890  # Expiration timestamp
    }
    
    Args:
        data: Dictionary containing user_id and role
    
    Returns:
        Encoded JWT token string (three parts separated by dots)
    
    Example:
        >>> token = create_access_token({"user_id": "123", "role": "admin"})
        >>> print(token)
        'eyJ0eXAiOiJKV1QiLCJhbGc...'
    
    How JWT works:
    1. Header: Algorithm and token type
    2. Payload: User data + expiration
    3. Signature: Prevents tampering (signed with SECRET_KEY)
    
    Format: base64(header).base64(payload).signature
    
    Frontend usage:
        Authorization: Bearer <token>
    """
    to_encode = data.copy()
    
    # Add expiration time
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    
    # Encode and sign token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict]:
    """
    Verify and decode a JWT token.
    
    Checks:
    1. Token signature is valid (hasn't been tampered with)
    2. Token hasn't expired
    3. Token format is correct
    
    Args:
        token: JWT token string from Authorization header
    
    Returns:
        Decoded token payload if valid, None if invalid/expired
    
    Example:
        >>> token = create_access_token({"user_id": "123", "role": "admin"})
        >>> payload = verify_token(token)
        >>> print(payload)
        {'user_id': '123', 'role': 'admin', 'exp': 1234567890}
        
        >>> bad_token = "invalid.token.here"
        >>> verify_token(bad_token)
        None
    
    Common failure reasons:
    - Token expired (exp timestamp passed)
    - Invalid signature (token was modified)
    - Malformed token (not proper JWT format)
    - Wrong SECRET_KEY used to decode
    """
    try:
        # Decode and verify token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        # Token is invalid, expired, or malformed
        return None


# ============================================================================
# Security Best Practices:
#
# 1. Never log passwords or tokens
# 2. Use HTTPS in production (encrypts token in transit)
# 3. Store SECRET_KEY in environment variable
# 4. Use secure random for SECRET_KEY generation
# 5. Set appropriate token expiration (not too long)
# 6. Implement token refresh mechanism for long sessions
# 7. Clear tokens on logout
# 8. Consider using httpOnly cookies instead of localStorage (XSS protection)
#
# Migration to Production:
# - Move SECRET_KEY to environment variable
# - Use Redis for token blacklist (revoked tokens)
# - Implement refresh tokens
# - Add rate limiting on auth endpoints
# - Log authentication attempts
# ============================================================================