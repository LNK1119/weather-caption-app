// DiaryListPage.tsx
import React, { useEffect, useState } from 'react';
import { fetchDiaryList, deleteDiary } from './api';
import { DiaryItem } from './types';

export function DiaryListPage({
  onSelectDiary,
  onBack,
  onGoWrite,
}: {
  onSelectDiary: (id: string) => void;
  onBack: () => void;
  onGoWrite: () => void;
}) {
  const [diaries, setDiaries] = useState<DiaryItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDiaries();
  }, []);  

  async function loadDiaries() {
    try {
      const list = await fetchDiaryList();
      setDiaries(list);
      setError(null);
    } catch {
      setError("일기 목록을 불러오는데 실패했습니다.");
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteDiary(id);
      loadDiaries();
    } catch {
      setError("삭제에 실패했습니다.");
    }
  }

  return (
    <div style={{ maxWidth: 700, margin: "30px auto", padding: 20, fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif" }}>
      <button
        onClick={onBack}
        style={{
          backgroundColor: "#00aaff",
          color: "white",
          border: "none",
          padding: "10px 15px",
          borderRadius: 8,
          cursor: "pointer",
          marginBottom: 20,
          fontWeight: "bold",
          transition: "background-color 0.3s"
        }}
        onMouseEnter={e => (e.currentTarget.style.backgroundColor = "#008ecc")}
        onMouseLeave={e => (e.currentTarget.style.backgroundColor = "#00aaff")}
      >
        메인으로
      </button>

      <h2 style={{ color: "#00aaff", marginBottom: 15 }}>일기 목록</h2>
      {error && <p style={{ color: "red" }}>{error}</p>}

      <ul style={{ listStyle: "none", padding: 0 }}>
        {diaries.map(d => (
          <li
            key={d.id}
            style={{
              padding: "12px 15px",
              marginBottom: 10,
              backgroundColor: "#e8f4fc",
              borderRadius: 10,
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              cursor: "pointer"
            }}
            onClick={() => onSelectDiary(d.id)}
          >
            <div>
              <strong>{d.title}</strong> <br />
              <small style={{ color: "#555" }}>
                {new Date(d.created_at).toLocaleString()} - {d.weather}
              </small>
            </div>
            <button
              onClick={e => {
                e.stopPropagation();
                handleDelete(d.id);
              }}
              style={{
                backgroundColor: "#ff5555",
                border: "none",
                color: "white",
                borderRadius: 8,
                padding: "6px 12px",
                cursor: "pointer",
                fontWeight: "bold",
                transition: "background-color 0.3s"
              }}
              onMouseEnter={e => (e.currentTarget.style.backgroundColor = "#cc4444")}
              onMouseLeave={e => (e.currentTarget.style.backgroundColor = "#ff5555")}
            >
              삭제
            </button>
          </li>
        ))}
      </ul>

      <button
        onClick={onGoWrite}
        style={{
          marginTop: 30,
          width: "100%",
          padding: "12px 0",
          fontSize: 18,
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
        새 일기 작성
      </button>
    </div>
  );
}
