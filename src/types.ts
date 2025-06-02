// types.ts
export interface DiaryItem {
  id: string;
  title: string;
  content?: string;
  weather: string;
  caption?: string;
  created_at: string;
}

export interface WeatherCaption {
  weather: string;
  caption: string;
  details: Record<string, any>;
}
