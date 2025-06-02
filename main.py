# -*- coding: utf-8 -*-
from fastapi import FastAPI, Query, UploadFile, File, HTTPException, Body, Path
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
import datetime
from typing import List
import os
from dotenv import load_dotenv
from pymongo import MongoClient, errors
from dateutil import parser
import httpx
import xmltodict
from pytz import timezone
from bson import ObjectId

# .env 파일 로드
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME_1 = os.getenv("COLLECTION_NAME_1")
COLLECTION_NAME_2 = os.getenv("COLLECTION_NAME_2")

# MongoDB 연결 (예외 처리 포함)
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()  # 연결 확인
    db = client[DB_NAME]
    collection1 = db[COLLECTION_NAME_1]
    collection2 = db[COLLECTION_NAME_2]
except errors.ServerSelectionTimeoutError as e:
    print(f"MongoDB 연결 실패: {e}")
    collection1 = None  # DB 연결 실패 시 None 처리
    collection2 = None  # DB 연결 실패 시 None 처리

app = FastAPI()

# 날씨별 캡션 사전
weather_captions = {
    "sunny": "맑고 화창한 하루예요. 어디론가 훌쩍 떠나보는 건 어때요?",
    "partly_cloudy": "구름이 조금 있지만, 바깥 활동엔 무리 없을 것 같아요!",
    "cloudy": "하늘이 잔뜩 흐렸네요. 조용한 실내 활동이 잘 어울리는 날이에요.",
    "rainy": "비가 오고 있어요. 우산 챙기고 발걸음 조심하세요!",
    "shower": "갑작스런 소나기가 내릴 수 있어요. 짧은 외출도 우산은 필수!",
    "snowy": "눈이 내려요. 포근한 옷차림과 따뜻한 음료를 곁들여보세요!"
}

# Pydantic 모델 정의
class CaptionItem(BaseModel):
    weather: str
    caption: str
    created_at: datetime.datetime

class DiarySaveRequest(BaseModel):
    title: str
    content: str
    lat: float  # 위도 추가
    lon: float  # 경도 추가
    weather: str = None  # API 내에서 채울 예정
    caption: str = None  # API 내에서 채울 예정
    created_at: datetime.datetime = None


class CaptionSaveRequest(BaseModel):
    weather: str
    caption: str

# 캡션 저장 함수 (MongoDB에 캡션 저장)
def insert_caption(item: CaptionItem):
    if collection1 is None:
        raise HTTPException(status_code=500, detail="DB 연결이 되어 있지 않습니다.")
    item_dict = item.dict()
    # created_at 은 datetime -> isoformat 문자열로 변환
    item_dict["created_at"] = item_dict["created_at"].isoformat()
    try:
        collection1.insert_one(item_dict)
    except Exception as e:
        print(f"캡션 DB 저장 오류: {e}")
        raise HTTPException(status_code=500, detail=f"캡션 DB 저장 실패: {e}")

# 일기 저장 함수
def insert_diary(item: DiarySaveRequest):
    if collection2 is None:
        raise HTTPException(status_code=500, detail="DB 연결이 되어 있지 않습니다.")
    item_dict = item.dict()
    if item_dict.get("created_at") is None:
        item_dict["created_at"] = datetime.datetime.now(timezone("Asia/Seoul")).isoformat()
    else:
        item_dict["created_at"] = item_dict["created_at"].isoformat()
    try:
        collection2.insert_one(item_dict)
    except Exception as e:
        print(f"DB 저장 오류: {e}")
        raise HTTPException(status_code=500, detail=f"DB 저장 실패: {e}")


# 기상청 API 설정
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
VILAGE_FORECAST_URL = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"

# 위경도 → 격자 변환 함수
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

# 기상청 API에서 받아온 데이터로 날씨 상태를 파싱하는 함수
def parse_weather_response(items):
    for item in items:
        category = item.get("category")
        fcstValue = item.get("fcstValue")

        if category == "PTY":
            if fcstValue == "1":  # 비
                return "rainy"
            elif fcstValue in ["2", "3"]:  # 비/눈, 눈
                return "snowy"
            elif fcstValue == "4":  # 소나기
                return "shower"
        elif category == "SKY":
            if fcstValue == "1":
                return "sunny"
            elif fcstValue == "3":
                return "partly_cloudy"
            elif fcstValue == "4":
                return "cloudy"
    return "sunny"

# 상세 날씨 정보 파싱 함수 (온도, 습도 등)
def parse_weather_details(items):
    temps, winds, hums, skies, precs = [], [], [], [], []
    for item in items:
        category = item.get("category")
        value = item.get("fcstValue")

        if category == "TMP":
            try:
                temps.append(float(value))
            except:
                pass
        elif category == "WSD":
            try:
                winds.append(float(value))
            except:
                pass
        elif category == "REH":
            try:
                hums.append(int(value))
            except:
                pass
        elif category == "SKY":
            skies.append(value)
        elif category == "PTY":
            precs.append(value)

    def avg(lst):
        return round(sum(lst) / len(lst), 1) if lst else None

    temp_min = min(temps) if temps else None
    temp_max = max(temps) if temps else None
    wind_min = min(winds) if winds else None
    wind_max = max(winds) if winds else None
    humidity_avg = avg(hums)

    description = {}
    description["Temperature"] = f"{temp_min}~{temp_max}°C" if temp_min is not None else "기온 정보 없음"
    description["WindSpeed"] = f"{wind_min}~{wind_max}m/s" if wind_min is not None else "풍속 정보 없음"
    description["Humidity"] = f"평균 {humidity_avg}%" if humidity_avg is not None else "습도 정보 없음"

    if "1" in precs:
        description["PrecipitationProbability"] = "비가 올 가능성 있음"
    elif "2" in precs:
        description["PrecipitationProbability"] = "비 또는 눈이 내릴 가능성 있음"
    elif "3" in precs:
        description["PrecipitationProbability"] = "눈이 올 가능성 있음"
    else:
        description["PrecipitationProbability"] = "강수 예상 없음"

    description["Precipitation"] = "0~1mm" if precs else "강수량 정보 없음"

    if "4" in skies:
        description["SkyCondition"] = "흐림"
    elif "3" in skies:
        description["SkyCondition"] = "구름 많음"
    elif "1" in skies:
        description["SkyCondition"] = "맑음"
    else:
        description["SkyCondition"] = "정보 없음"

    return description

# 위도/경도 기반으로 기상청 API 호출하여 날씨 캡션 생성
@app.get("/weather/caption", summary="위치 기반 날씨 캡션 생성")
async def get_weather_caption(lat: float = Query(..., description="위도"),
                              lon: float = Query(..., description="경도")):
    nx, ny = convert_to_grid(lat, lon)

    params = {
        "serviceKey": WEATHER_API_KEY,
        "pageNo": "1",
        "numOfRows": "100",
        "dataType": "JSON",
        "base_date": datetime.datetime.now(timezone("Asia/Seoul")).strftime("%Y%m%d"),
        "base_time": "0500",
        "nx": str(nx),
        "ny": str(ny),
    }

    async with httpx.AsyncClient() as client_http:
        response = await client_http.get(VILAGE_FORECAST_URL, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="기상청 API 호출 실패")

    result = response.json()
    items = result.get("response", {}).get("body", {}).get("items", {}).get("item", [])
    if not items:
        raise HTTPException(status_code=404, detail="기상 정보가 없습니다.")

    weather_state = parse_weather_response(items)
    caption_text = weather_captions.get(weather_state, "오늘도 좋은 하루 보내세요!")

    details = parse_weather_details(items)

    result_json = {
        "weather": weather_state,
        "caption": caption_text,
        "details": details
    }
    return JSONResponse(content=jsonable_encoder(result_json))

# 캡션 저장 API
@app.post("/caption/save", summary="캡션 저장")
async def save_caption(data: CaptionSaveRequest):
    item = CaptionItem(
        weather=data.weather,
        caption=data.caption,
        created_at=datetime.datetime.now(timezone("Asia/Seoul"))
    )
    insert_caption(item)
    return {"message": "캡션이 저장되었습니다."}

# 일기 저장 API
@app.post("/diary/save", summary="일기 저장")
async def save_diary(data: DiarySaveRequest):
    # 1) 위도/경도 받아서 기상청 API 호출 -> 날씨 상태, 캡션 얻기
    nx, ny = convert_to_grid(data.lat, data.lon)

    params = {
        "serviceKey": WEATHER_API_KEY,
        "pageNo": "1",
        "numOfRows": "100",
        "dataType": "JSON",
        "base_date": datetime.datetime.now(timezone("Asia/Seoul")).strftime("%Y%m%d"),
        "base_time": "0500",
        "nx": str(nx),
        "ny": str(ny),
    }

    async with httpx.AsyncClient() as client_http:
        response = await client_http.get(VILAGE_FORECAST_URL, params=params)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="기상청 API 호출 실패")

    result = response.json()
    items = result.get("response", {}).get("body", {}).get("items", {}).get("item", [])
    if not items:
        raise HTTPException(status_code=404, detail="기상 정보가 없습니다.")

    weather_state = parse_weather_response(items)
    caption_text = weather_captions.get(weather_state, "오늘도 좋은 하루 보내세요!")

    # 2) 날씨와 캡션을 data에 추가
    data.weather = weather_state
    data.caption = caption_text

    # 3) created_at 필드 없으면 현재 시간으로 채우기
    if data.created_at is None:
        data.created_at = datetime.datetime.now(timezone("Asia/Seoul"))

    insert_diary(data)
    return {"message": "일기가 저장되었습니다.", "weather": data.weather, "caption": data.caption}

# 일기 목록 조회 API
@app.get("/diary/list", summary="일기 목록 조회")
async def get_diary_list():
    if collection2 is None:
        raise HTTPException(status_code=500, detail="DB 연결이 되어 있지 않습니다.")
    try:
        docs = list(collection2.find({}, {"_id": 1, "title": 1, "weather": 1, "caption": 1, "created_at": 1}))
        result = []
        for d in docs:
            result.append({
                "id": str(d["_id"]),
                "title": d.get("title"),
                "weather": d.get("weather"),
                "caption": d.get("caption"),
                "created_at": d.get("created_at")
            })
        return {"diaries": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일기 조회 실패: {e}")


# 특정 일기 삭제 API
@app.delete("/diary/delete/{diary_id}", summary="일기 삭제")
async def delete_diary(diary_id: str = Path(..., description="삭제할 일기의 ObjectId 문자열")):
    if collection2 is None:
        raise HTTPException(status_code=500, detail="DB 연결이 되어 있지 않습니다.")
    try:
        oid = ObjectId(diary_id)
    except Exception:
        raise HTTPException(status_code=400, detail="유효하지 않은 ID 형식입니다.")

    result = collection2.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="해당 ID의 일기를 찾을 수 없습니다.")
    return {"message": "일기가 삭제되었습니다."}
