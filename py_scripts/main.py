import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Ensure required static directories exist before mounting
for folder in ["static", "image_assets", "webpages"]:
    os.makedirs(folder, exist_ok=True)

# Mount static asset folders
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/image_assets", StaticFiles(directory="image_assets"), name="image_assets")

# Page routes
@app.get("/")
async def serve_home():
    return FileResponse("webpages/index.html")

@app.get("/login")
async def serve_login():
    return FileResponse("webpages/login.html")

@app.get("/payment")
async def serve_payment():
    return FileResponse("webpages/payment.html")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("py_scripts.main:app", host="0.0.0.0", port=port, reload=True)