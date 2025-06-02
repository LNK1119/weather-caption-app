// App.tsx (최상위)
import React, { useState } from 'react';
import { MainPage } from './MainPage';
import { DiaryListPage } from './DiaryListPage';
import { DiaryDetailPage } from './DiaryDetailPage';

export function App() {
  const [page, setPage] = useState<"main" | "list" | "detail">("main");
  const [selectedDiaryId, setSelectedDiaryId] = useState<string | null>(null);

  return (
    <div style={{ maxWidth: 600, margin: "auto", padding: 20 }}>
      {page === "main" && <MainPage onGoDiaryList={() => setPage("list")} />}
      {page === "list" && (
        <DiaryListPage
          onSelectDiary={id => {
            setSelectedDiaryId(id);
            setPage("detail");
          }}
          onBack={() => setPage("main")}
        />
      )}
      {page === "detail" && selectedDiaryId && (
        <DiaryDetailPage id={selectedDiaryId} onBack={() => setPage("list")} />
      )}
    </div>
  );
}
