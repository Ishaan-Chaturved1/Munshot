from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI()

# ✅ Enable CORS (important for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = "data"


@app.get("/")
def home():
    return {"message": "API is running"}


@app.get("/data")
def get_data():
    try:
        # Load products
        with open(os.path.join(DATA_DIR, "products.json"), "r", encoding="utf-8") as f:
            products = json.load(f)

        # Load reviews
        with open(os.path.join(DATA_DIR, "reviews.json"), "r", encoding="utf-8") as f:
            reviews = json.load(f)

        # Load brand summaries
        with open(os.path.join(DATA_DIR, "brand_summary.json"), "r", encoding="utf-8") as f:
            summaries = json.load(f)

        return {
            "products": products,
            "reviews": reviews,
            "summaries": summaries
        }

    except FileNotFoundError as e:
        return {
            "error": "Data files missing on server",
            "details": str(e)
        }

    except Exception as e:
        return {
            "error": "Something went wrong",
            "details": str(e)
        }