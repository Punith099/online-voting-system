from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import json
import uuid
from datetime import datetime, timedelta

# Initialize FastAPI app
app = FastAPI(title="Quiz Application API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/auth/signup")
async def signup(data: dict):
    try:
        # Validate required fields
        required = ["name", "email", "password", "role"]
        if not all(field in data for field in required):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields"
            )
        
        # Read existing users
        try:
            with open("data/users.json", "r") as f:
                users = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            users = []

        # Check if email exists
        if any(user["email"] == data["email"] for user in users):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user
        user = {
            "id": str(uuid.uuid4()),
            "name": data["name"],
            "email": data["email"],
            "password": data["password"],  # In production, hash this!
            "role": data["role"]
        }
        
        # Add to users list
        users.append(user)
        
        # Write back to file
        with open("data/users.json", "w") as f:
            json.dump(users, f, indent=2)

        return {"message": "User created successfully", "user": user}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup failed: {str(e)}"
        )

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Quiz Application API"}