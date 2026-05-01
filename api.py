from fastapi import FastAPI
import json
import os

app = FastAPI()

DATA_PATH = "data/dashboard.json"


@app.get("/")
def home():
    return {"message": "API is running"}


@app.get("/data")
def get_data():
    if not os.path.exists(DATA_PATH):
        return {"error": "No data available"}

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)