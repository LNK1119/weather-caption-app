// api.ts - API 호출 함수 정리
import axios from 'axios';
import { WeatherCaption } from './types';
import { DiaryItem } from './types';

const API_BASE = "https://weather-caption-123-e9eegwdzcvfddta8.koreasouth-01.azurewebsites.net";

export async function fetchWeatherCaption(lat: number, lon: number) {
  const res = await axios.get<WeatherCaption>(`${API_BASE}/weather/caption`, { params: { lat, lon } });
  return res.data;
}

export async function fetchDiaryList() {
  const res = await axios.get<{ diaries: DiaryItem[] }>(`${API_BASE}/diary/list`);
  return res.data.diaries;
}

export async function fetchDiaryDetail(id: string) {
  const res = await axios.get<DiaryItem>(`${API_BASE}/diary/list`); // 백엔드 수정 필요. 일단 리스트에서 id로 필터링 가능
  return res.data;
}

export async function deleteDiary(id: string) {
  await axios.delete(`${API_BASE}/diary/delete/${id}`);
}

export async function saveDiary(data: { title: string; content: string; lat: number; lon: number }) {
  const res = await axios.post(`${API_BASE}/diary/save`, data);
  return res.data;
}
