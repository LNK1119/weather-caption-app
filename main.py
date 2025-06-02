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
import httpx
import xmltodict
from pytz import timezone

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
    "sunny": "맑고 화창한 하루예요. 어디론가 훌쩍 떠나보는 건 어때요?",
    "partly_cloudy": "구름이 조금 있지만, 바깥 활동엔 무리 없을 것 같아요!",
    "cloudy": "하늘이 잔뜩 흐렸네요. 조용한 실내 활동이 잘 어울리는 날이에요.",
    "rainy": "비가 오고 있어요. 우산 챙기고 발걸음 조심하세요!",
    "shower": "갑작스런 소나기가 내릴 수 있어요. 짧은 외출도 우산은 필수!",
    "snowy": "눈이 내려요. 포근한 옷차림과 따뜻한 음료를 곁들여보세요!"
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

def parse_weather_response(items):
    for item in items:
        category = item.get("category")
        fcstValue = item.get("fcstValue")
        print(f"category={category}, fcstValue={fcstValue}")  # 디버깅용 출력
        
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
    
    return "sunny"  # 기본값


def parse_weather_details(items):
    temps, winds, hums, skies, precs = [], [], [], [], []
    for item in items:
        category = item.get("category")
        value = item.get("fcstValue")

        if category == "T1H":  # 기온
            temps.append(float(value))
        elif category == "WSD":  # 풍속
            winds.append(float(value))
        elif category == "REH":  # 습도
            hums.append(int(value))
        elif category == "SKY":
            skies.append(value)
        elif category == "PTY":
            precs.append(value)

    def avg(values): return round(sum(values) / len(values), 1) if values else None

    description = f"기온은 {min(temps)}~{max(temps)}°C입니다. "
    description += f"풍속은 {min(winds)}~{max(winds)}m/s입니다. "
    description += f"습도는 평균 {avg(hums)}%입니다. "
    if "3" in precs or "2" in precs or "1" in precs:
        description += "비가 내릴 가능성이 있습니다. "
    else:
        description += "강수는 예상되지 않습니다. "
    if "4" in skies:
        description += "하늘 상태는 흐림입니다."
    elif "3" in skies:
        description += "하늘 상태는 구름 많음입니다."
    else:
        description += "하늘 상태는 맑음입니다."

    return description

@app.get("/caption")
def generate_caption(weather: str = Query(..., description="현재 날씨 (sunny, rainy, etc.)")):
    caption = weather_captions.get(weather.lower(), "날씨에 맞는 캡션을 찾을 수 없어요.")
    
    # ✅ 괄호 닫기 수정
    item = CaptionItem(
        weather=weather,
        caption=caption,
        created_at=datetime.datetime.now(timezone("Asia/Seoul"))
    )

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
    item = CaptionItem(
        weather=data.weather,
        caption=data.caption,
        created_at=datetime.datetime.now(timezone("Asia/Seoul"))
    )
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
        item = CaptionItem(
            weather=predicted_weather,
            caption=caption,
            created_at=datetime.datetime.now(timezone("Asia/Seoul"))
        )
        insert_caption(item)

        return JSONResponse(content=jsonable_encoder(item))
    except Exception as e:
        print(f"이미지 캡션 생성 실패: {e}")
        raise HTTPException(status_code=400, detail="유효한 이미지 파일을 업로드해주세요.")


@app.get("/caption/location")
async def caption_from_location(lat: float = Query(...), lon: float = Query(...)):
    if collection is None:
        raise HTTPException(status_code=500, detail="DB 연결이 되어 있지 않습니다.")

    def get_valid_base_time():
        now = datetime.datetime.now(timezone("Asia/Seoul"))
        current_time = int(now.strftime("%H%M"))
        base_times = ["2300", "2000", "1700", "1400", "1100", "0800", "0500", "0200"]
        candidates = []
        for bt in base_times:
            if current_time >= int(bt):
                candidates.append((now.strftime("%Y%m%d"), bt))
        if not candidates:
            yesterday = (now - datetime.timedelta(days=1)).strftime("%Y%m%d")
            candidates.append((yesterday, "2300"))
        return candidates

    try:
        nx, ny = convert_to_grid(lat, lon)
        base_time_candidates = get_valid_base_time()

        for base_date, base_time in base_time_candidates:
            try:
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
                        },
                        timeout=10.0
                    )
                response.raise_for_status()
                data = xmltodict.parse(response.text)
                response_data = data.get("response")
                header = response_data.get("header", {})
                result_code = header.get("resultCode")
                result_msg = header.get("resultMsg")

                if result_code == "00":
                    body = response_data.get("body", {})
                    items = body.get("items", {}).get("item")
                    if items is None:
                        continue
                    if isinstance(items, dict):
                        items = [items]

                    # ������ 가장 가까운 forecast time의 데이터만 추출
                    latest_time = max(item['fcstTime'] for item in items)
                    latest_items = [item for item in items if item['fcstTime'] == latest_time]

                    predicted_weather = parse_weather_response(latest_items)
                    caption = weather_captions.get(predicted_weather, "날씨에 맞는 캡션을 찾을 수 없어요.")
                    description = parse_weather_details(latest_items)
                    
                    item = CaptionItem(
                        weather=predicted_weather,
                        caption=caption,
                        created_at=datetime.datetime.now(timezone("Asia/Seoul"))
                    )
                    insert_caption(item)

                    return JSONResponse(content=jsonable_encoder({
                        "caption_item": item,
                        "description": description
                    }))

                elif result_msg == "NO_DATA":
                    print(f"[기상청] NO_DATA: {base_date} {base_time}, 다음 시도 중...")
                    continue
                else:
                    raise HTTPException(status_code=500, detail=f"기상청 API 오류: {result_msg}")

            except httpx.HTTPStatusError as e:
                print(f"HTTP 오류: {e}")
                continue
            except httpx.RequestError as e:
                print(f"요청 오류: {e}")
                raise HTTPException(status_code=503, detail="기상청 API 서버에 연결할 수 없습니다.")
            except Exception as e:
                print(f"기상 정보 파싱 실패: {e}")
                continue

        raise HTTPException(status_code=404, detail="기상 정보를 찾을 수 없습니다. (모든 시간 실패)")

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"위치 기반 캡션 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"위치 기반 캡션 생성 실패: {e}")
