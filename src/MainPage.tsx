import React, { useEffect, useState } from 'react';
import { fetchWeatherCaption } from './api';
import { WeatherCaption } from './types';

export function MainPage({ onGoDiaryList }: { onGoDiaryList: () => void }) {
  const [weatherData, setWeatherData] = useState<WeatherCaption | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    navigator.geolocation.getCurrentPosition(async (pos) => {
      try {
        const data = await fetchWeatherCaption(pos.coords.latitude, pos.coords.longitude);
        setWeatherData(data);
      } catch (e) {
        setError("날씨 정보를 불러오는데 실패했습니다.");
      }
    }, () => setError("위치 정보를 가져올 수 없습니다."));
  }, []);

  return (
    <div style={{
      maxWidth: 480,
      margin: "40px auto",
      padding: 20,
      borderRadius: 12,
      boxShadow: "0 0 15px rgba(0, 170, 255, 0.3)",
      background: "linear-gradient(135deg, #e0f7ff, #ffffff)"
    }}>
      <h1 style={{ color: "#00aaff", textAlign: "center", marginBottom: 20 }}>오늘의 날씨</h1>
      
      {error && <p style={{ color: "red", textAlign: "center" }}>{error}</p>}

      {weatherData ? (
        <div style={{ textAlign: "center", fontSize: 18, color: "#333" }}>
          <p>날씨: <strong>{weatherData.weather}</strong></p>
          <p>오늘 날씨의 한마디:</p>
          <p style={{ fontStyle: "italic", color: "#0077cc", marginBottom: 20 }}>{weatherData.caption}</p>

          <div style={{
            backgroundColor: "rgba(255, 255, 255, 0.7)",
            borderRadius: 8,
            padding: "15px 10px",
            textAlign: "left",
            fontSize: 15,
            lineHeight: 1.6,
            boxShadow: "inset 0 0 5px rgba(0,0,0,0.05)"
          }}>
            <p><strong>🌡 온도:</strong> {weatherData.details.Temperature}</p>
            <p><strong>💨 풍속:</strong> {weatherData.details.WindSpeed}</p>
            <p><strong>💧 습도:</strong> {weatherData.details.Humidity}</p>
            <p><strong>🌧 강수 확률:</strong> {weatherData.details.PrecipitationProbability}</p>
            <p><strong>☔ 강수량:</strong> {weatherData.details.Precipitation}</p>
            <p><strong>☁️ 하늘 상태:</strong> {weatherData.details.SkyCondition}</p>
          </div>
        </div>
      ) : (
        <p style={{ textAlign: "center", color: "#666" }}>위치 정보를 가져오는 중...</p>
      )}

      <button
        onClick={onGoDiaryList}
        style={{
          marginTop: 30,
          display: "block",
          width: "100%",
          padding: "12px 0",
          fontSize: 16,
          fontWeight: "bold",
          color: "white",
          backgroundColor: "#00aaff",
          border: "none",
          borderRadius: 8,
          cursor: "pointer",
          transition: "background-color 0.3s"
        }}
        onMouseEnter={e => (e.currentTarget.style.backgroundColor = "#008ecc")}
        onMouseLeave={e => (e.currentTarget.style.backgroundColor = "#00aaff")}
      >
        일기 목록 보기
      </button>
    </div>
  );
}
