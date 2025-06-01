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
from pymongo import MongoClient
from dateutil import parser  # datetime 파싱을 위해 필요

# .env 파일 로드
load_dotenv()

# 환경 변수 가져오기
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

# MongoDB 연결
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

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

# 공통 insert 함수 (datetime을 문자열로 변환)
def insert_caption(item: CaptionItem):
    item_dict = item.dict()
    item_dict["created_at"] = item_dict["created_at"].isoformat()
    collection.insert_one(item_dict)

# 1. 날씨 기반 캡션 생성
@app.get("/caption")
def generate_caption(weather: str = Query(..., description="현재 날씨 (sunny, rainy, etc.)")):
    caption = weather_captions.get(weather.lower(), "날씨에 맞는 캡션을 찾을 수 없어요.")
    item = CaptionItem(weather=weather, caption=caption, created_at=datetime.datetime.now())
    insert_caption(item)
    return JSONResponse(content=jsonable_encoder(item))

# 2. 수동 저장
class CaptionSaveRequest(BaseModel):
    weather: str
    caption: str

@app.post("/caption/save")
def save_caption(data: CaptionSaveRequest = Body(...)):
    item = CaptionItem(weather=data.weather, caption=data.caption, created_at=datetime.datetime.now())
    insert_caption(item)
    return {"message": "캡션 저장 완료", "item": jsonable_encoder(item)}

# 3. 히스토리 조회
@app.get("/caption/history", response_model=List[CaptionItem])
def get_caption_history():
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

# 4. 이미지 기반 캡션 생성
@app.post("/caption/image")
def caption_from_image(file: UploadFile = File(...)):
    try:
        contents = file.file.read()
        image = Image.open(io.BytesIO(contents))
        image.verify()

        predicted_weather = random.choice(list(weather_captions.keys()))
        caption = weather_captions.get(predicted_weather, "날씨에 맞는 캡션을 찾을 수 없어요.")
        item = CaptionItem(weather=predicted_weather, caption=caption, created_at=datetime.datetime.now())
        insert_caption(item)

        return JSONResponse(content=jsonable_encoder(item))

    except Exception:
        raise HTTPException(status_code=400, detail="유효한 이미지 파일을 업로드해주세요.")

# 5. 위치 기반 캡션 생성
@app.get("/caption/location")
def caption_from_location(lat: float = Query(...), lon: float = Query(...)):
    mock_weather = random.choice(list(weather_captions.keys()))
    caption = weather_captions[mock_weather]
    item = CaptionItem(weather=mock_weather, caption=caption, created_at=datetime.datetime.now())
    insert_caption(item)
    return JSONResponse(content=jsonable_encoder(item))
