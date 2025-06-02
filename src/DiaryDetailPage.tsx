// DiaryDetailPage.tsx
import React, { useEffect, useState } from 'react';
import { DiaryItem } from './types';
import { fetchDiaryList, deleteDiary } from './api';

export function DiaryDetailPage({ id, onBack }: { id: string; onBack: () => void }) {
  const [diary, setDiary] = useState<DiaryItem | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDetail() {
      try {
        // 백엔드에 상세 API 없으므로 리스트에서 필터링
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

  if (error) return <p style={{ color: "red" }}>{error}</p>;
  if (!diary) return <p>로딩 중...</p>;

  return (
    <div>
      <button onClick={onBack}>목록으로</button>
      <button onClick={handleDelete} style={{ float: "right" }}>삭제</button>
      <h2>{diary.title}</h2>
      <p>{diary.content}</p>
      <p>날씨: {diary.weather}</p>
      <p>캡션: {diary.caption}</p>
      <p>작성일: {new Date(diary.created_at).toLocaleString()}</p>
    </div>
  );
}
