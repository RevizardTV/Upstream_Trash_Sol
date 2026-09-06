import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Mount the 'webpages' folder to serve static files (CSS, images, JS)
app.mount("/static", StaticFiles(directory="webpages"), name="static")

@app.get("/", response_class=FileResponse)
async def read_index():
    # Points to webpages/index.html from the root folder
    return FileResponse("webpages/index.html")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    # Note the module path syntax: py_scripts.main:app
    uvicorn.run("py_scripts.main:app", host="0.0.0.0", port=port, reload=True)