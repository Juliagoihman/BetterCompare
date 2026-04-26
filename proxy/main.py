from fastapi import FastAPI

app = FastAPI(title="BetterCompare Proxy")

@app.get("/")
def home():
    return {
        "name": "BetterCompare",
        "message": "Proxy is running"
    }
