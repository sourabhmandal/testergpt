from fastapi import FastAPI, Request
import logging
from src.github.router import github_router

app = FastAPI()
logger = logging.getLogger("main")


app.include_router(github_router)


@app.get("/")
async def root():
    message = "This is an example of FastAPI with Jinja2 - go to /hi/<name> to see a template rendered"
    return {"message": message}


@app.get("/env")
async def env(req: Request):
    env = req.scope["env"]
    message = f"Here is an example of getting an environment variable: {env.MESSAGE}"
    return {"message": message}