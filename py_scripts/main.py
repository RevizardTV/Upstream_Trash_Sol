import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Mount the static directory to serve /css and /js
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount image_assets directory for SVGs or photos if needed
app.mount("/image_assets", StaticFiles(directory="image_assets"), name="image_assets")

# Serve individual page views from /webpages/
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