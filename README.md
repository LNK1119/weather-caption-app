chat gpt의 도움을 받았습니다.
# 🌤️ 날씨 일기 웹 애플리케이션   
***
## 1. 프로젝트 개요 
날씨 보고 일기 쓰는 웹 앱입니다.  
오늘 날씨에 따라 어떤 일이 있었는지 작성하는 애플리케이션입니다! 
기상청 API를 써서 실시간 날씨를 가져오고, 그걸 기반으로 간단한 일기 쓰는 기능이 있습니다.

- 백엔드는 FastAPI, python으로 만들었습니다.
- 프론트는 react기반 입니다.  
- 데이터는 MongoDB에 저장됩니다. (Azure Cosmos DB 사용).

  
***
## 1. 기술 스택 
백엔드: FastAPI + Python   
프론트엔드: React (CRA로 시작, 도커는 안 씀)   
DB: MongoDB (Azure Cosmos DB 사용)   
날씨 API: 기상청 단기예보 API 
배포: Azure Web App + GitHub Actions + Docker   
기타: GitHub Actions로 CI/CD 자동화 해놨습니다   


***
## 3. 주요 기능 및 작동 방식 
#### 현재 날씨 확인
사용자의 위도/경도를 기반으로 기상청 API를 호출해 날씨 정보를 가져옵니다.
#### 날씨 일기 작성
사용자 입력으로 일기 내용을 작성하고, 현재 날씨와 함께 MongoDB에 저장됩니다.
#### 날씨 일기 목록 조회
날짜별로 작성된 일기를 리스트로 확인할 수 있습니다.
#### 날씨 일기 삭제
이미 작성한 일기를 삭제할 수 있습니다.

***
## 4. 로컬 실행 방법
#### 백엔드 실행 (Docker 사용)   
git clone https://github.com/LNK1119/weather-caption-app.git   
cd weather-caption-app/backend  

env 파일에 
MONGO_URI=몽고DB_접속_URI
DB_NAME=몽고DB 이름
COLLECTION_NAME_1=captions
COLLECTION_NAME_2=diaries
WEATHER_API_KEY=기상청_API_키

docker build -t weather-caption-backend .
docker run -p 8000:8000 --env-file .env weather-caption-backend

#### 프론트엔드 실행 (Docker 미사용)   
cd weather-caption-app  
npm install   
npm start   
src/api.ts 파일에서 백엔드 주소 변경 필요
***
## 5. 배포 방법   
#### 백엔드
GitHub Actions → DockerHub → Azure Web App이 pull해서 자동 배포

####  프론트엔드
npm run build → 정적 파일 배포 (Azure에 직접 올림)
