from fastapi import FastAPI, Request, Query
from pydantic import BaseModel
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime
from typing import List, Any

load_dotenv()

# MongoDB setup
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]
collection = db[os.getenv("COLLECTION_NAME")]

app = FastAPI()

class SensorData(BaseModel):
    suhu: float
    kelembapan: float
    ph: float
    nitrogen: int
    kalium: int
    fosfor: int
    konduktivitas: int

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}


@app.get("/get")
async def get_data(
    items: int = Query(10, gt=0),
    page: int = Query(1, gt=0)
):
    skip = (page - 1) * items
    cursor = collection.find().skip(skip).limit(items)
    data = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        data.append(doc)
    total = collection.count_documents({})
    return {
        "page": page,
        "items": items,
        "total": total,
        "data": data
    }

@app.post("/kirim-data")
async def kirim_data(data: SensorData):
    document = {
        "suhu": data.suhu,
        "kelembapan": data.kelembapan,
        "ph": data.ph,
        "nitrogen": data.nitrogen,
        "kalium": data.kalium,
        "fosfor": data.fosfor,
        "konduktivitas": data.konduktivitas,
        "inputed_at": datetime.now()
    }
    result = collection.insert_one(document)
    return {"status": "OK", "id": str(result.inserted_id)}
