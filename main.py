from fastapi import FastAPI, Request, Query
from pydantic import BaseModel
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime
from typing import List, Any
import requests

load_dotenv()

# MongoDB setup
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]
class SensorData(BaseModel):
    device: int = 1
    suhu: float = 0
    kelembapan: float = 0
    ph: float = 0
    nitrogen: int = 0
    kalium: int = 0
    fosfor: int = 0
    konduktivitas: int = 0
    latitude: float = None
    longitude: float = None
    
collection = db[os.getenv("COLLECTION_NAME")]
collection2 = db[os.getenv("COLLECTION_NAME2")]
collection3 = db[os.getenv("COLLECTION_NAME3")]
collection4 = db[os.getenv("COLLECTION_NAME4")]
collection5 = db[os.getenv("COLLECTION_NAME5")]
collection6 = db[os.getenv("COLLECTION_NAME6")]
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}


@app.get("/get")
async def get_data(
    items: int = Query(10, gt=0),
    page: int = Query(1, gt=0),
    device: int = Query(None, description="Filter by device (1-6)"),
    suhu: float = Query(None),
    kelembapan: float = Query(None),
    ph: float = Query(None),
    nitrogen: int = Query(None),
    kalium: int = Query(None),
    fosfor: int = Query(None),
    konduktivitas: int = Query(None),
    latitude: float = Query(None),
    longitude: float = Query(None)
):
    skip = (page - 1) * items
    query = {}
    if suhu is not None:
        query["suhu"] = suhu
    if kelembapan is not None:
        query["kelembapan"] = kelembapan
    if ph is not None:
        query["ph"] = ph
    if nitrogen is not None:
        query["nitrogen"] = nitrogen
    if kalium is not None:
        query["kalium"] = kalium
    if fosfor is not None:
        query["fosfor"] = fosfor
    if konduktivitas is not None:
        query["konduktivitas"] = konduktivitas
    if latitude is not None:
        query["latitude"] = latitude
    if longitude is not None:
        query["longitude"] = longitude

    # Pilih collection berdasarkan device, atau semua jika device None
    collections = [collection, collection2, collection3, collection4, collection5, collection6]
    if device is not None and 1 <= device <= 6:
        collections = [collections[device-1]]

    data = []
    total = 0
    for col in collections:
        cursor = col.find(query).sort("inputed_at", -1)
        total += col.count_documents(query)
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            doc["collection"] = col.name
            data.append(doc)

    # Sort gabungan dan paginasi manual
    data = sorted(data, key=lambda x: x.get("inputed_at", datetime.min), reverse=True)
    paged_data = data[skip:skip+items]

    return {
        "page": page,
        "items": items,
        "total": total,
        "data": paged_data
    }

@app.post("/kirim-data")
async def kirim_data(data: SensorData):
    document = {
        "device": data.device,
        "suhu": data.suhu,
        "kelembapan": data.kelembapan,
        "ph": data.ph,
        "nitrogen": data.nitrogen,
        "kalium": data.kalium,
        "fosfor": data.fosfor,
        "konduktivitas": data.konduktivitas,
        "latitude": data.latitude,
        "longitude": data.longitude,
        "inputed_at": datetime.now()
    }
    # Pilih collection berdasarkan device
    if data.device == 1:
        result = collection.insert_one(document)
    elif data.device == 2:
        result = collection2.insert_one(document)
    elif data.device == 3:
        result = collection3.insert_one(document)
    elif data.device == 4:
        result = collection4.insert_one(document)
    elif data.device == 5:
        result = collection5.insert_one(document)   
    elif data.device == 6:
        result = collection6.insert_one(document)
    else:
        return {"status": "Status Code: 404, Collection Not Found"}
    return {"status": "OK", "id": str(result.inserted_id)}
