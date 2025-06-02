import React, { useEffect, useState } from 'react';
import { DiaryItem } from './types';
import { fetchDiaryList, deleteDiary } from './api';

export function DiaryDetailPage({ id, onBack }: { id: string; onBack: () => void }) {
  const [diary, setDiary] = useState<DiaryItem | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDetail() {
      try {
        const list = await fetchDiaryList();
        const found = list.find(d => d.id === id);
        if (!found) setError("해당 일기를 찾을 수 없습니다.");
        else setDiary(found);
      } catch {
        setError("일기 상세 조회 실패");
      }
    }
    loadDetail();
  }, [id]);

  async function handleDelete() {
    if (!id) return;
    try {
      await deleteDiary(id);
      onBack();
    } catch {
      setError("삭제 실패");
    }
  }

  if (error) return <p style={{ color: "red", textAlign: "center" }}>{error}</p>;
  if (!diary) return <p style={{ textAlign: "center" }}>로딩 중...</p>;

  return (
    <div style={{
      maxWidth: 480,
      margin: "40px auto",
      padding: 24,
      borderRadius: 12,
      background: "linear-gradient(135deg, #e0f7ff, #ffffff)",
      boxShadow: "0 0 15px rgba(0, 170, 255, 0.3)"
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 20 }}>
        <button
          onClick={onBack}
          style={{
            padding: "8px 16px",
            fontSize: 14,
            borderRadius: 8,
            border: "none",
            backgroundColor: "#00aaff",
            color: "white",
            cursor: "pointer"
          }}
        >
          ← 목록으로
        </button>
        <button
          onClick={handleDelete}
          style={{
            padding: "8px 16px",
            fontSize: 14,
            borderRadius: 8,
            border: "none",
            backgroundColor: "#ff4d4d",
            color: "white",
            cursor: "pointer"
          }}
        >
          삭제
        </button>
      </div>

      <h2 style={{ color: "#0077cc", marginBottom: 10 }}>{diary.title}</h2>

      <div style={{
        backgroundColor: "rgba(255, 255, 255, 0.7)",
        padding: 15,
        borderRadius: 8,
        lineHeight: 1.6,
        marginBottom: 20
      }}>
        <p>{diary.content}</p>
      </div>

      <div style={{
        fontSize: 15,
        color: "#333",
        backgroundColor: "rgba(255,255,255,0.6)",
        padding: 12,
        borderRadius: 8
      }}>
        <p><strong>🌦 날씨:</strong> {diary.weather}</p>
        <p><strong>📝 날씨 캡션:</strong> <em>{diary.caption}</em></p>
        <p><strong>🕒 작성일:</strong> {new Date(diary.created_at).toLocaleString()}</p>
      </div>
    </div>
  );
}
