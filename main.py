from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/caption")
def generate_caption(weather: str = Query(..., description="현재 날씨 (sunny, rainy, etc.)")):
    captions = {
        "sunny": "햇살 가득한 날, 나들이 가기 딱 좋은 날씨예요!",
        "rainy": "비 오는 날, 창가에 앉아 차 한 잔의 여유를 즐겨보세요.",
        "cloudy": "구름이 많은 하루예요. 산책에는 좋을지도 몰라요!",
        "snowy": "하얀 눈이 내려요. 포근한 옷차림을 추천해요!"
    }
    caption = captions.get(weather.lower(), "날씨에 맞는 캡션을 찾을 수 없어요.")
    return JSONResponse(content={"weather": weather, "caption": caption})