import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import contants, utils, auth, users
from fastapi.staticfiles import StaticFiles

app = FastAPI()
origins = ["<http://localhost:8000>"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(utils.router, prefix="/api")
app.include_router(contants.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")

docs_path = os.path.join(os.path.dirname(__file__), "docs", "_build", "html")
app.mount("/docs-html", StaticFiles(directory=docs_path, html=True), name="docs-html")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
