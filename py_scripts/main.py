import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Mount the 'static' folder to serve CSS and JS assets
app.mount("/static", StaticFiles(directory="static"), name="static")

# Endpoint 1: Home Page
@app.get("/")
async def read_home():
    return FileResponse("templates/index.html")

# Endpoint 2: Login Page
@app.get("/login")
async def read_login():
    return FileResponse("templates/login.html")

# Endpoint 3: Payment / Payout Dashboard Page
@app.get("/payment")
async def read_payment():
    return FileResponse("templates/payment.html")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("py_scripts.main:app", host="0.0.0.0", port=port, reload=True)