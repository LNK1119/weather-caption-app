// MainPage.tsx
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
    <div>
      <h1>오늘의 날씨</h1>
      {error && <p style={{color:"red"}}>{error}</p>}
      {weatherData ? (
        <>
          <p>날씨: {weatherData.weather}</p>
          <p>캡션: {weatherData.caption}</p>
          {/* 상세 정보도 필요하면 추가 표시 */}
        </>
      ) : (
        <p>위치 정보를 가져오는 중...</p>
      )}
      <button onClick={onGoDiaryList}>일기 목록 보기</button>
    </div>
  );
}
