from fastapi import FastAPI, Request, HTTPException
from app.config import API_SECRET_TOKEN
from app.xray_control import add_user

app = FastAPI()

@app.get("/add-user")
def add_user_api(request: Request, email: str, token: str):
    if token != API_SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Access denied")
    
    link = add_user(email)
    if link is None:
        return {"error": "Пользователь уже существует."}
    return {"link": link}
