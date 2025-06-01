from fastapi import FastAPI, Query, UploadFile, File, HTTPException, Body
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
import datetime
from typing import List
import io
from PIL import Image
import random
import os
from dotenv import load_dotenv
from pymongo import MongoClient, errors
from dateutil import parser

# .env 파일 로드
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

# MongoDB 연결 (예외 처리 포함)
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()  # 연결 확인
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
except errors.ServerSelectionTimeoutError as e:
    print(f"MongoDB 연결 실패: {e}")
    collection = None  # DB 연결 실패 시 None 처리

app = FastAPI()

weather_captions = {
    "sunny": "햇살 가득한 날, 나들이 가기 딱 좋은 날씨예요!",
    "rainy": "비 오는 날, 창가에 앉아 차 한 잔의 여유를 즐겨보세요.",
    "cloudy": "구름이 많은 하루예요. 산책에는 좋을지도 몰라요!",
    "snowy": "하얀 눈이 내려요. 포근한 옷차림을 추천해요!"
}

class CaptionItem(BaseModel):
    weather: str
    caption: str
    created_at: datetime.datetime

def insert_caption(item: CaptionItem):
    if collection is None:
        raise HTTPException(status_code=500, detail="DB 연결이 되어 있지 않습니다.")
    item_dict = item.dict()
    item_dict["created_at"] = item_dict["created_at"].isoformat()
    try:
        collection.insert_one(item_dict)
    except Exception as e:
        print(f"DB 저장 오류: {e}")
        raise HTTPException(status_code=500, detail=f"DB 저장 실패: {e}")

@app.get("/caption")
def generate_caption(weather: str = Query(..., description="현재 날씨 (sunny, rainy, etc.)")):
    caption = weather_captions.get(weather.lower(), "날씨에 맞는 캡션을 찾을 수 없어요.")
    item = CaptionItem(weather=weather, caption=caption, created_at=datetime.datetime.now())
    try:
        insert_caption(item)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"캡션 생성 실패: {e}")
    return JSONResponse(content=jsonable_encoder(item))

class CaptionSaveRequest(BaseModel):
    weather: str
    caption: str

@app.post("/caption/save")
def save_caption(data: CaptionSaveRequest = Body(...)):
    item = CaptionItem(weather=data.weather, caption=data.caption, created_at=datetime.datetime.now())
    try:
        insert_caption(item)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"캡션 저장 실패: {e}")
    return {"message": "캡션 저장 완료", "item": jsonable_encoder(item)}

@app.get("/caption/history", response_model=List[CaptionItem])
def get_caption_history():
    if collection is None:
        raise HTTPException(status_code=500, detail="DB 연결이 되어 있지 않습니다.")
    try:
        docs = collection.find().sort("created_at", -1).limit(100)
        result = []
        for doc in docs:
            created_at = doc.get("created_at")
            if isinstance(created_at, str):
                created_at = parser.parse(created_at)
            result.append(CaptionItem(
                weather=doc["weather"],
                caption=doc["caption"],
                created_at=created_at
            ))
        return result
    except Exception as e:
        print(f"히스토리 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"히스토리 조회 실패: {e}")

@app.post("/caption/image")
def caption_from_image(file: UploadFile = File(...)):
    if collection is None:
        raise HTTPException(status_code=500, detail="DB 연결이 되어 있지 않습니다.")
    try:
        contents = file.file.read()
        image = Image.open(io.BytesIO(contents))
        image.verify()

        predicted_weather = random.choice(list(weather_captions.keys()))
        caption = weather_captions.get(predicted_weather, "날씨에 맞는 캡션을 찾을 수 없어요.")
        item = CaptionItem(weather=predicted_weather, caption=caption, created_at=datetime.datetime.now())
        insert_caption(item)

        return JSONResponse(content=jsonable_encoder(item))
    except Exception as e:
        print(f"이미지 캡션 생성 실패: {e}")
        raise HTTPException(status_code=400, detail="유효한 이미지 파일을 업로드해주세요.")

@app.get("/caption/location")
def caption_from_location(lat: float = Query(...), lon: float = Query(...)):
    if collection is None:
        raise HTTPException(status_code=500, detail="DB 연결이 되어 있지 않습니다.")
    try:
        mock_weather = random.choice(list(weather_captions.keys()))
        caption = weather_captions[mock_weather]
        item = CaptionItem(weather=mock_weather, caption=caption, created_at=datetime.datetime.now())
        insert_caption(item)
        return JSONResponse(content=jsonable_encoder(item))
    except Exception as e:
        print(f"위치 기반 캡션 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"위치 기반 캡션 생성 실패: {e}")
