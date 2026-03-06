from datetime import datetime, timedelta # Import tools for date and time calculations
from typing import Any, Union # Import for flexible data type definitions
from jose import jwt # Import tool to create and decode JSON Web Tokens (secure IDs)
from passlib.context import CryptContext # Import tool for secure password hashing
from app.core.config import settings # Import project settings (secret keys, algorithms)

# Initialize the password hashing tool using the 'bcrypt' algorithm
# This ensures passwords are encrypted and follow modern security standards
pwd_context = CryptContext(schemes=["bcrypt"], deprecat   ed="auto") 

# Function to check if a plain-text password matches its hashed (encrypted) version
def verify_password(plain_password: str, hashed_password: str) -> bool: 
    # Returns True if they match, False otherwise
    return pwd_context.verify(plain_password, hashed_password) 

# Function to convert a plain-text password into a secure, unreadable hash
def get_password_hash(password: str) -> str: 
    # This hash is what gets stored in the database
    return pwd_context.hash(password) 

# Function to create a short-term Access Token used for making API requests
def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str: 
    # Set the expiration time for the token
    if expires_delta: 
        expire = datetime.utcnow() + expires_delta 
    else: 
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES) 
    
    # Store the user's ID ('sub') and the expiration time ('exp') inside the token
    to_encode = {"sub": str(subject), "exp": expire} 
    # Cryptographically sign the data so it cannot be tampered with
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM) 
    return encoded_jwt 

# Function to create a long-term Refresh Token used to get new Access Tokens
def create_refresh_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str: 
    # Set the expiration time (usually much longer than access tokens, e.g., days/years)
    if expires_delta: 
        expire = datetime.utcnow() + expires_delta 
    else: 
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS) 
    
    # Identify this as a 'refresh' type token and store user ID
    to_encode = {"sub": str(subject), "exp": expire, "type": "refresh"} 
    # Sign and return the token
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM) 
    return encoded_jwt 
