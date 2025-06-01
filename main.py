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
        
# 기상청 API 설정값
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
VILAGE_FORECAST_URL = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"

# 위경도 → 격자 변환 함수 (기상청 API는 격자 좌표 필요)
def convert_to_grid(lat, lon):
    import math
    RE = 6371.00877
    GRID = 5.0
    SLAT1 = 30.0
    SLAT2 = 60.0
    OLON = 126.0
    OLAT = 38.0
    XO = 43
    YO = 136
    DEGRAD = math.pi / 180.0
    re = RE / GRID
    slat1 = SLAT1 * DEGRAD
    slat2 = SLAT2 * DEGRAD
    olon = OLON * DEGRAD
    olat = OLAT * DEGRAD
    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = math.pow(sf, sn) * math.cos(slat1) / sn
    ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = re * sf / math.pow(ro, sn)
    ra = math.tan(math.pi * 0.25 + lat * DEGRAD * 0.5)
    ra = re * sf / math.pow(ra, sn)
    theta = lon * DEGRAD - olon
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn
    x = int(ra * math.sin(theta) + XO + 0.5)
    y = int(ro - ra * math.cos(theta) + YO + 0.5)
    return x, y

# 초단기예보로부터 날씨 정보 파싱
def parse_weather_response(items):
    weather = "sunny"
    for item in items:
        category = item.get("category")
        fcstValue = item.get("fcstValue")
        if category == "PTY":  # 강수형태 (0: 없음, 1: 비, 2: 비/눈, 3: 눈, 4: 소나기)
            if fcstValue in ["1", "4"]:
                return "rainy"
            elif fcstValue in ["2", "3"]:
                return "snowy"
        elif category == "SKY":  # 하늘 상태 (1: 맑음, 3: 구름많음, 4: 흐림)
            if fcstValue == "1":
                weather = "sunny"
            elif fcstValue == "3":
                weather = "cloudy"
            elif fcstValue == "4":
                weather = "cloudy"
    return weather        

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
async def caption_from_location(lat: float = Query(...), lon: float = Query(...)):
    if collection is None:
        raise HTTPException(status_code=500, detail="DB 연결이 되어 있지 않습니다.")
    try:
        now = datetime.datetime.now()
        base_date = now.strftime("%Y%m%d")
        base_time = now.strftime("%H00")
        if int(base_time[:2]) < 2:
            base_date = (now - datetime.timedelta(days=1)).strftime("%Y%m%d")
            base_time = "2300"

        nx, ny = convert_to_grid(lat, lon)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                VILAGE_FORECAST_URL,
                params={
                    "serviceKey": WEATHER_API_KEY,
                    "dataType": "XML",
                    "numOfRows": 1000,
                    "pageNo": 1,
                    "base_date": base_date,
                    "base_time": base_time,
                    "nx": nx,
                    "ny": ny
                }
            )
        data = xmltodict.parse(response.text)
        items = data["response"]["body"]["items"]["item"]
        if isinstance(items, dict):
            items = [items]

        predicted_weather = parse_weather_response(items)
        caption = weather_captions.get(predicted_weather, "날씨에 맞는 캡션을 찾을 수 없어요.")
        item = CaptionItem(weather=predicted_weather, caption=caption, created_at=datetime.datetime.now())
        insert_caption(item)

        return JSONResponse(content=jsonable_encoder(item))
    except Exception as e:
        print(f"위치 기반 캡션 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"위치 기반 캡션 생성 실패: {e}")
