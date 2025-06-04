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
collection = db[os.getenv("COLLECTION_NAME")]

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
# Mapping: index ke topic id (isi sesuai kebutuhan group Telegram Anda)
TELEGRAM_TOPIC_IDS = {
    "suhu": int(os.getenv("TELEGRAM_TOPIC_ID_SUHU", 0)),
    "kelembapan": int(os.getenv("TELEGRAM_TOPIC_ID_KELEMBAPAN", 0)),
    "ph": int(os.getenv("TELEGRAM_TOPIC_ID_PH", 0)),
    "nitrogen": int(os.getenv("TELEGRAM_TOPIC_ID_NITROGEN", 0)),
    "fosfor": int(os.getenv("TELEGRAM_TOPIC_ID_FOSFOR", 0)),
    "kalium": int(os.getenv("TELEGRAM_TOPIC_ID_KALIUM", 0)),
    "konduktivitas": int(os.getenv("TELEGRAM_TOPIC_ID_KONDUKTIVITAS", 0)),
}

def send_telegram_alert(param, value, message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    topic_id = TELEGRAM_TOPIC_IDS.get(param)
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    # Hanya tambahkan message_thread_id jika topic_id > 0
    if topic_id is not None and topic_id > 0:
        payload["message_thread_id"] = topic_id
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        pass  # Optional: log error

class SensorData(BaseModel):
    suhu: float
    kelembapan: float
    ph: float
    nitrogen: int
    kalium: int
    fosfor: int
    konduktivitas: int

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}


@app.get("/get")
async def get_data(
    items: int = Query(10, gt=0),
    page: int = Query(1, gt=0),
    suhu: float = Query(None),
    kelembapan: float = Query(None),
    ph: float = Query(None),
    nitrogen: int = Query(None),
    kalium: int = Query(None),
    fosfor: int = Query(None),
    konduktivitas: int = Query(None)
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

    cursor = collection.find(query).sort("inputed_at", -1).skip(skip).limit(items)
    data = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        data.append(doc)
    total = collection.count_documents(query)
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
    # Alert logic
    # 1. Suhu
    if data.suhu < 20:
        send_telegram_alert(
            "suhu", data.suhu,
            "🌡️ <b>ALERT: Suhu Terlalu Rendah</b>\n"
            f"Nilai terdeteksi: <b>{data.suhu}°C</b> (Ideal: 25–32°C)\n"
            "Risiko: Pertumbuhan tanaman melambat.\n"
            "<i>Solusi: Periksa sistem pemanas atau lakukan penutupan lahan sementara.</i>"
        )
    elif data.suhu > 35:
        send_telegram_alert(
            "suhu", data.suhu,
            "🌡️ <b>ALERT: Suhu Terlalu Tinggi</b>\n"
            f"Nilai terdeteksi: <b>{data.suhu}°C</b> (Ideal: 25–32°C)\n"
            "Risiko: Tanaman mengalami stres panas.\n"
            "<i>Solusi: Tingkatkan irigasi, gunakan peneduh, atau lakukan penyiraman pagi/sore.</i>"
        )
    # 2. Kelembapan
    if data.kelembapan < 40:
        send_telegram_alert(
            "kelembapan", data.kelembapan,
            "💧 <b>ALERT: Kelembapan Terlalu Rendah</b>\n"
            f"Nilai terdeteksi: <b>{data.kelembapan}%</b> (Ideal: 60–80% RH)\n"
            "Risiko: Tanah/udara terlalu kering.\n"
            "<i>Solusi: Tingkatkan frekuensi penyiraman atau gunakan mulsa.</i>"
        )
    elif data.kelembapan > 90:
        send_telegram_alert(
            "kelembapan", data.kelembapan,
            "💧 <b>ALERT: Kelembapan Terlalu Tinggi</b>\n"
            f"Nilai terdeteksi: <b>{data.kelembapan}%</b> (Ideal: 60–80% RH)\n"
            "Risiko: Potensi jamur/busuk akar meningkat.\n"
            "<i>Solusi: Perbaiki drainase dan kurangi penyiraman.</i>"
        )
    # 3. pH
    if data.ph < 4.5:
        send_telegram_alert(
            "ph", data.ph,
            "⚗️ <b>ALERT: pH Terlalu Asam</b>\n"
            f"Nilai terdeteksi: <b>{data.ph}</b> (Ideal: 4.5–6.5 untuk sawit)\n"
            "Risiko: Potensi racun Al, pertumbuhan akar terganggu.\n"
            "<i>Solusi: Aplikasikan dolomit/kapur pertanian sesuai dosis rekomendasi.</i>"
        )
    elif data.ph > 7.5:
        send_telegram_alert(
            "ph", data.ph,
            "⚗️ <b>ALERT: pH Terlalu Basa</b>\n"
            f"Nilai terdeteksi: <b>{data.ph}</b> (Ideal: 4.5–6.5 untuk sawit)\n"
            "Risiko: Kekurangan mikronutrien.\n"
            "<i>Solusi: Tambahkan bahan organik atau gunakan pupuk asam.</i>"
        )
    # 4. Nitrogen
    if data.nitrogen < 150:
        send_telegram_alert(
            "nitrogen", data.nitrogen,
            "🧪 <b>ALERT: Defisiensi Nitrogen</b>\n"
            f"Nilai terdeteksi: <b>{data.nitrogen} mg/kg</b> (Ideal: >200 mg/kg)\n"
            "Risiko: Daun menguning, pertumbuhan lambat.\n"
            "<i>Solusi: Tambahkan pupuk N sesuai rekomendasi agronomis.</i>"
        )
    elif data.nitrogen > 500:
        send_telegram_alert(
            "nitrogen", data.nitrogen,
            "🧪 <b>ALERT: Nitrogen Berlebih</b>\n"
            f"Nilai terdeteksi: <b>{data.nitrogen} mg/kg</b> (Ideal: >200 mg/kg)\n"
            "Risiko: Daun terlalu hijau, potensi pembusukan meningkat.\n"
            "<i>Solusi: Kurangi aplikasi pupuk N, lakukan monitoring lanjutan.</i>"
        )
    # 5. Fosfor
    if data.fosfor < 10:
        send_telegram_alert(
            "fosfor", data.fosfor,
            "🧪 <b>ALERT: Kekurangan Fosfor</b>\n"
            f"Nilai terdeteksi: <b>{data.fosfor} mg/kg</b> (Ideal: >15 mg/kg)\n"
            "Risiko: Akar pendek, pertumbuhan terganggu.\n"
            "<i>Solusi: Tambahkan pupuk P (misal SP-36) sesuai dosis.</i>"
        )
    elif data.fosfor > 200:
        send_telegram_alert(
            "fosfor", data.fosfor,
            "🧪 <b>ALERT: Fosfor Berlebih</b>\n"
            f"Nilai terdeteksi: <b>{data.fosfor} mg/kg</b> (Ideal: >15 mg/kg)\n"
            "Risiko: Gangguan penyerapan mikronutrien.\n"
            "<i>Solusi: Hindari aplikasi pupuk P berlebih, lakukan pencucian tanah jika perlu.</i>"
        )
    # 6. Kalium
    if data.kalium < 60:
        send_telegram_alert(
            "kalium", data.kalium,
            "🧪 <b>ALERT: Kekurangan Kalium</b>\n"
            f"Nilai terdeteksi: <b>{data.kalium} mg/kg</b> (Ideal: >100 mg/kg)\n"
            "Risiko: Daun terbakar, pertumbuhan terganggu.\n"
            "<i>Solusi: Tambahkan pupuk K (misal KCl) sesuai rekomendasi.</i>"
        )
    elif data.kalium > 300:
        send_telegram_alert(
            "kalium", data.kalium,
            "🧪 <b>ALERT: Kalium Berlebih</b>\n"
            f"Nilai terdeteksi: <b>{data.kalium} mg/kg</b> (Ideal: >100 mg/kg)\n"
            "Risiko: Gangguan penyerapan Mg dan Ca.\n"
            "<i>Solusi: Kurangi aplikasi pupuk K, lakukan monitoring lanjutan.</i>"
        )
    # 7. Konduktivitas
    if data.konduktivitas < 150:
        send_telegram_alert(
            "konduktivitas", data.konduktivitas,
            "⚡ <b>ALERT: Konduktivitas Terlalu Rendah</b>\n"
            f"Nilai terdeteksi: <b>{data.konduktivitas} µS/cm</b> (Ideal: 200–1000 µS/cm)\n"
            "Risiko: Tanah miskin nutrisi.\n"
            "<i>Solusi: Evaluasi kebutuhan pemupukan dan tambahkan nutrisi sesuai analisis tanah.</i>"
        )
    elif data.konduktivitas > 2000:
        send_telegram_alert(
            "konduktivitas", data.konduktivitas,
            "⚡ <b>ALERT: Konduktivitas Terlalu Tinggi</b>\n"
            f"Nilai terdeteksi: <b>{data.konduktivitas} µS/cm</b> (Ideal: 200–1000 µS/cm)\n"
            "Risiko: Salinitas tinggi, potensi racun akar.\n"
            "<i>Solusi: Lakukan pencucian tanah (leaching) dan monitoring EC secara berkala.</i>"
        )

    result = collection.insert_one(document)
    return {"status": "OK", "id": str(result.inserted_id)}
