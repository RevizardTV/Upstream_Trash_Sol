import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Mount the 'webpages' folder to serve CSS, JS, and static assets
# Accessible via: http://localhost:8000/static/styles.css and http://localhost:8000/static/app.js
app.mount("/static", StaticFiles(directory="webpages"), name="static")

@app.get("/")
async def read_index():
    # Return index.html when users hit the base root URL
    return FileResponse("webpages/index.html")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    # Correct module path for uvicorn when executed directly
    uvicorn.run("py_scripts.main:app", host="0.0.0.0", port=port, reload=True)