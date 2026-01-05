from auth import hash_password, verify_password
import json

def test_password_auth():
    # Test with the default admin password
    password = "admin123"
    hashed = hash_password(password)
    print(f"Password: {password}")
    print(f"Generated hash: {hashed}")
    
    # Test verification
    print(f"\nVerifying password '{password}':")
    is_valid = verify_password(password, hashed)
    print(f"Password valid: {is_valid}")
    
    # Test stored hash from users.json
    with open("data/users.json", "r") as f:
        users = json.load(f)
        admin = next(u for u in users if u["email"] == "admin@example.com")
        stored_hash = admin["password_hash"]
        
    print(f"\nStored admin hash: {stored_hash}")
    print(f"Verifying 'admin123' against stored hash:")
    print(verify_password("admin123", stored_hash))
    print(f"Verifying 'Admin123!' against stored hash:")
    print(verify_password("Admin123!", stored_hash))

if __name__ == "__main__":
    test_password_auth()