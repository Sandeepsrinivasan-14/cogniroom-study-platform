from fastapi import HTTPException

# ... keep the rest of your imports and code above

@app.post("/auth/register")
def register(user_in: UserCreate):
    # TEMP: pretend registration always succeeds
    if user_in.email != "alice@example.com":
        # keep it simple so you always know the test user
        raise HTTPException(status_code=400, detail="Only alice@example.com is allowed in demo")
    return {"message": "User registered", "email": user_in.email}


@app.post("/auth/login", response_model=Token)
def login(user_in: UserLogin):
    # TEMP: hard-coded demo user
    if user_in.email != "alice@example.com" or user_in.password != "password123":
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = create_access_token({"sub": "1"})
    return {"access_token": access_token, "token_type": "bearer"}
