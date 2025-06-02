// DiaryListPage.tsx
import React, { useEffect, useState } from 'react';
import { fetchDiaryList, deleteDiary, saveDiary } from './api';
import { DiaryItem } from './types';

export function DiaryListPage({ onSelectDiary, onBack }: { onSelectDiary: (id: string) => void; onBack: () => void }) {
  const [diaries, setDiaries] = useState<DiaryItem[]>([]);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [error, setError] = useState<string | null>(null);

  // 위치는 작성 시점에 다시 받아오거나, 고정 좌표로 예시
  const lat = 37.5665;
  const lon = 126.9780;

  useEffect(() => {
    loadDiaries();
  }, []);

  async function loadDiaries() {
    try {
      const list = await fetchDiaryList();
      setDiaries(list);
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

  async function handleSave() {
    if (!title || !content) {
      setError("제목과 내용을 모두 입력하세요.");
      return;
    }
    try {
      await saveDiary({ title, content, lat, lon });
      setTitle("");
      setContent("");
      loadDiaries();
    } catch {
      setError("일기 저장에 실패했습니다.");
    }
  }

  return (
    <div>
      <button onClick={onBack}>메인으로</button>
      <h2>일기 목록</h2>
      {error && <p style={{color:"red"}}>{error}</p>}
      <ul>
        {diaries.map(d => (
          <li key={d.id}>
            <span onClick={() => onSelectDiary(d.id)} style={{ cursor: "pointer" }}>
              {d.title} - {new Date(d.created_at).toLocaleString()} - {d.weather}
            </span>
            <button onClick={() => handleDelete(d.id)} style={{ marginLeft: "10px" }}>삭제</button>
          </li>
        ))}
      </ul>

      <h3>새 일기 작성</h3>
      <input value={title} onChange={e => setTitle(e.target.value)} placeholder="제목" /><br />
      <textarea value={content} onChange={e => setContent(e.target.value)} placeholder="내용" /><br />
      <button onClick={handleSave}>저장</button>
    </div>
  );
}
