import React, { useState } from 'react';
import { saveDiary } from './api';

interface Props {
  onSaveSuccess: () => void;
  onBack: () => void;
}

export function DiaryWritePage({ onSaveSuccess, onBack }: Props) {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [error, setError] = useState<string | null>(null);

  const lat = 37.5665;
  const lon = 126.9780;

  async function handleSave() {
    if (!title || !content) {
      setError("제목과 내용을 모두 입력하세요.");
      return;
    }
    try {
      await saveDiary({ title, content, lat, lon });
      setTitle("");
      setContent("");
      onSaveSuccess();
    } catch {
      setError("일기 저장에 실패했습니다.");
    }
  }

  return (
    <div
      style={{
        backgroundColor: "#f0f8ff", // 하늘색 배경
        padding: "30px", // 내부 전체 여백 증가
        borderRadius: "12px",
        boxShadow: "0 4px 10px rgba(0,0,0,0.05)",
        fontFamily: "Arial, sans-serif"
      }}
    >
      <button
        onClick={onBack}
        style={{
          backgroundColor: "transparent",
          border: "none",
          color: "#0288d1",
          cursor: "pointer",
          marginBottom: "10px",
          fontSize: "16px"
        }}
      >
        ← 돌아가기
      </button>

      <h2 style={{ color: "#0277bd", marginBottom: "15px" }}>새 일기 작성</h2>

      {error && <p style={{ color: "red" }}>{error}</p>}

      <input
        value={title}
        onChange={e => setTitle(e.target.value)}
        placeholder="제목"
        style={{
          width: "100%",
          padding: "12px",
          borderRadius: "6px",
          border: "1px solid #b3e5fc",
          marginBottom: "12px",
          fontSize: "16px",
          boxSizing: "border-box" // padding 포함한 전체 너비 유지
        }}
      />

      <textarea
        value={content}
        onChange={e => setContent(e.target.value)}
        placeholder="내용"
        rows={6}
        style={{
          width: "100%",
          padding: "12px",
          borderRadius: "6px",
          border: "1px solid #b3e5fc",
          marginBottom: "20px",
          fontSize: "16px",
          resize: "vertical",
          boxSizing: "border-box"
        }}
      />

      <button
        onClick={handleSave}
        style={{
          backgroundColor: "#03a9f4",
          color: "white",
          padding: "10px 20px",
          border: "none",
          borderRadius: "6px",
          cursor: "pointer",
          fontSize: "16px"
        }}
      >
        저장
      </button>
    </div>
  );
}
