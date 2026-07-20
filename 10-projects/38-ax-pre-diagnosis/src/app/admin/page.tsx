'use client';

import { useState, useEffect } from 'react';

interface SessionItem {
  id: string;
  token: string;
  participant_name: string | null;
  status: string;
  started_at: string;
  completed_at: string | null;
  current_question: number;
}

interface ChatAnswer {
  id: string;
  raw_answer: string;
  is_follow_up: boolean;
  question_id: string;
  created_at: string;
}

interface DesireAnalysis {
  confirmed_summary?: {
    ai_usage_level?: string;
    participation_reason?: string;
    expected_change?: string;
    target_task?: string;
    ai_role_level?: string;
    satisfaction_criteria?: string;
    first_action?: string;
  };
  desire_analysis?: {
    underlying_desire?: string;
    frustration_source?: string;
    ideal_future_state?: string;
    gap_analysis?: string;
    motivation_type?: string;
    readiness_level?: number;
    education_leverage_points?: string[];
    risk_factors?: string[];
    personalized_recommendation?: string;
  };
  additional_opinions?: string | null;
}

const ADMIN_CODE = typeof window !== 'undefined' ? '' : '';

export default function AdminPage() {
  const [code, setCode] = useState('');
  const [authed, setAuthed] = useState(false);
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<{ session: SessionItem & { interview_answers: ChatAnswer[] }; analysis: DesireAnalysis | null } | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [desireResult, setDesireResult] = useState<DesireAnalysis | null>(null);

  async function login() {
    const res = await fetch(`/api/admin/sessions?code=${code}`);
    if (res.ok) {
      const data = await res.json();
      setSessions(data.sessions);
      setAuthed(true);
    } else {
      alert('인증 코드가 올바르지 않습니다.');
    }
  }

  async function loadDetail(id: string) {
    setSelectedId(id);
    setDesireResult(null);
    const res = await fetch(`/api/admin/sessions?code=${code}&id=${id}`);
    if (res.ok) {
      const data = await res.json();
      setDetail(data);
    }
  }

  async function runDesireAnalysis(sessionId: string) {
    setAnalyzing(true);
    try {
      const res = await fetch('/api/admin/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, sessionId }),
      });
      if (res.ok) {
        const data = await res.json();
        setDesireResult(data);
      }
    } finally {
      setAnalyzing(false);
    }
  }

  useEffect(() => {
    if (selectedId && detail && !desireResult && detail.session.status === 'completed') {
      runDesireAnalysis(selectedId);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId, detail]);

  function formatDate(d: string) {
    return new Date(d).toLocaleString('ko-KR', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  }

  function buildChatPairs(answers: ChatAnswer[]) {
    const pairs: { ai: string; user: string }[] = [];
    const sorted = [...answers].sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());

    let currentAi = '';
    for (const a of sorted) {
      if (a.is_follow_up) {
        currentAi = a.raw_answer;
      } else {
        pairs.push({ ai: currentAi, user: a.raw_answer });
        currentAi = '';
      }
    }
    return pairs;
  }

  // --- 로그인 화면 ---
  if (!authed) {
    return (
      <div className="min-h-dvh bg-[#f4f3f8] flex items-center justify-center px-6">
        <div className="w-full max-w-sm">
          <div className="text-center mb-8">
            <p className="text-xs font-bold tracking-wider text-[#6C5CE7] mb-2">RXR-AX-EDU</p>
            <h1 className="text-xl font-extrabold text-gray-900">관리자 대시보드</h1>
          </div>
          <div className="bg-white rounded-2xl p-6 shadow-sm">
            <input
              type="password"
              value={code}
              onChange={e => setCode(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && login()}
              placeholder="관리자 코드 입력"
              className="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:border-[#6C5CE7] mb-4"
            />
            <button
              onClick={login}
              className="w-full py-3 bg-[#6C5CE7] text-white rounded-xl font-bold text-sm hover:bg-[#5a4bd6] transition-colors"
            >
              접속
            </button>
          </div>
        </div>
      </div>
    );
  }

  // --- 상세 보기 ---
  if (selectedId && detail) {
    const { session } = detail;
    const answers = session.interview_answers || [];
    const chatPairs = buildChatPairs(answers);
    const cs = desireResult?.confirmed_summary;
    const da = desireResult?.desire_analysis;

    return (
      <div className="min-h-dvh bg-[#f4f3f8]">
        <div className="max-w-3xl mx-auto px-4 py-8">

          {/* 네비 */}
          <button
            onClick={() => { setSelectedId(null); setDetail(null); setDesireResult(null); }}
            className="flex items-center gap-1.5 text-sm text-[#6C5CE7] font-semibold mb-6 hover:underline"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
            목록으로
          </button>

          {/* 헤더 */}
          <div className="text-center mb-8">
            <p className="text-xs font-bold tracking-wider text-[#6C5CE7] mb-1">RXR-AX-EDU</p>
            <h1 className="text-2xl font-extrabold text-gray-900">사전진단 결과 리포트</h1>
          </div>

          {/* ===== 1. 참여자 정보 ===== */}
          <div className="bg-white rounded-2xl p-6 shadow-sm mb-6">
            <h2 className="text-xs font-bold text-[#6C5CE7] tracking-wider mb-4 pb-2 border-b-2 border-[#ede9fe]">참여자 정보</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-5">
              <div>
                <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1">이름</p>
                <p className="text-base font-bold text-gray-900">{session.participant_name || '익명'}</p>
              </div>
              <div>
                <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1">상태</p>
                <p className="text-base font-bold text-[#6C5CE7]">
                  {session.status === 'completed' ? '완료' : session.status === 'in_progress' ? '진행중' : '시작'}
                </p>
              </div>
              <div>
                <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1">일시</p>
                <p className="text-base font-bold text-gray-900">{formatDate(session.started_at)}</p>
              </div>
              <div>
                <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1">소요시간</p>
                <p className="text-base font-bold text-gray-900">
                  {session.completed_at
                    ? `${Math.round((new Date(session.completed_at).getTime() - new Date(session.started_at).getTime()) / 60000)}분`
                    : '-'}
                </p>
              </div>
              <div>
                <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1">대화 턴</p>
                <p className="text-base font-bold text-gray-900">{chatPairs.length}턴</p>
              </div>
              <div>
                <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1">토큰</p>
                <p className="text-base font-bold text-gray-900 font-mono">{session.token}</p>
              </div>
            </div>
          </div>

          {/* ===== 2. 합의된 최종 써머리 ===== */}
          {analyzing && !desireResult && (
            <div className="bg-white rounded-2xl p-6 shadow-sm mb-6 text-center">
              <div className="flex items-center justify-center gap-2 text-sm text-gray-400 py-8">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                대화 내용을 분석하고 있습니다...
              </div>
            </div>
          )}

          {cs && (
            <div className="bg-white rounded-2xl p-6 shadow-sm mb-6">
              <h2 className="text-xs font-bold text-[#6C5CE7] tracking-wider mb-4 pb-2 border-b-2 border-[#ede9fe]">합의된 최종 의견</h2>
              <div className="space-y-4">
                {[
                  { num: '1', label: 'AI 사용 수준', value: cs.ai_usage_level },
                  { num: '2', label: '참여 이유', value: cs.participation_reason },
                  { num: '3', label: '기대하는 변화', value: cs.expected_change },
                  { num: '4', label: '적용 업무', value: cs.target_task },
                  { num: '5', label: 'AI 역할 수준', value: cs.ai_role_level },
                  { num: '6', label: '만족 기준', value: cs.satisfaction_criteria },
                  { num: '7', label: '첫 행동', value: cs.first_action },
                ].map(item => (
                  <div key={item.num} className="flex gap-3 items-start">
                    <span className="flex-none w-6 h-6 rounded-lg bg-[#6C5CE7] text-white text-xs font-bold flex items-center justify-center mt-0.5">{item.num}</span>
                    <div>
                      <p className="text-xs font-bold text-gray-400 mb-0.5">{item.label}</p>
                      <p className="text-sm text-gray-800 leading-relaxed">{item.value || '-'}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 추가 의견 */}
          {desireResult?.additional_opinions && (
            <div className="bg-[#f2f0fe] rounded-2xl p-6 mb-6">
              <h2 className="text-xs font-bold text-[#6C5CE7] tracking-wider mb-3">추가 의견 / 기대치</h2>
              <p className="text-sm text-gray-800 leading-relaxed">{desireResult.additional_opinions}</p>
            </div>
          )}

          {/* ===== 3. 희망·욕구 심층 분석 ===== */}
          {da && (
            <div className="bg-white rounded-2xl p-6 shadow-sm mb-6">
              <h2 className="text-xs font-bold text-[#6C5CE7] tracking-wider mb-4 pb-2 border-b-2 border-[#ede9fe]">희망·욕구 심층 분석</h2>
              <div className="space-y-5">

                <div className="bg-gradient-to-r from-[#6C5CE7] to-[#a29bfe] rounded-xl p-5 text-white">
                  <p className="text-[10px] font-bold uppercase tracking-wider opacity-70 mb-1">숨겨진 진짜 욕구</p>
                  <p className="text-sm leading-relaxed font-medium">{da.underlying_desire}</p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="bg-gray-50 rounded-xl p-4">
                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">불만·고통의 근원</p>
                    <p className="text-sm text-gray-700 leading-relaxed">{da.frustration_source}</p>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-4">
                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">이상적 업무 모습</p>
                    <p className="text-sm text-gray-700 leading-relaxed">{da.ideal_future_state}</p>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-xl p-4">
                  <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">갭 분석 (현재 ↔ 이상)</p>
                  <p className="text-sm text-gray-700 leading-relaxed">{da.gap_analysis}</p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="bg-gray-50 rounded-xl p-4">
                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">동기 유형</p>
                    <p className="text-sm text-gray-700 leading-relaxed">{da.motivation_type}</p>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-4">
                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">변화 준비도</p>
                    <div className="flex items-center gap-2 mt-1">
                      {[1, 2, 3, 4, 5].map(n => (
                        <span
                          key={n}
                          className={`w-8 h-8 rounded-lg text-xs font-bold flex items-center justify-center ${
                            n <= (da.readiness_level || 0) ? 'bg-[#6C5CE7] text-white' : 'bg-gray-200 text-gray-400'
                          }`}
                        >
                          {n}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {da.education_leverage_points && da.education_leverage_points.length > 0 && (
                  <div className="bg-[#f2f0fe] rounded-xl p-4">
                    <p className="text-[10px] font-bold text-[#6C5CE7] uppercase tracking-wider mb-2">교육 레버리지 포인트</p>
                    <ul className="space-y-1.5">
                      {da.education_leverage_points.map((p, i) => (
                        <li key={i} className="text-sm text-gray-700 leading-relaxed flex gap-2">
                          <span className="text-[#6C5CE7] flex-none">•</span>
                          {p}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {da.risk_factors && da.risk_factors.length > 0 && (
                  <div className="bg-red-50 rounded-xl p-4">
                    <p className="text-[10px] font-bold text-red-400 uppercase tracking-wider mb-2">위험 요소</p>
                    <ul className="space-y-1.5">
                      {da.risk_factors.map((r, i) => (
                        <li key={i} className="text-sm text-gray-700 leading-relaxed flex gap-2">
                          <span className="text-red-400 flex-none">!</span>
                          {r}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {da.personalized_recommendation && (
                  <div className="bg-[#6C5CE7] rounded-xl p-5 text-white">
                    <p className="text-[10px] font-bold uppercase tracking-wider opacity-70 mb-2">맞춤 교육 제안</p>
                    <p className="text-sm leading-relaxed">{da.personalized_recommendation}</p>
                  </div>
                )}

              </div>
            </div>
          )}

          {/* ===== 4. 대화 로그 ===== */}
          <div className="bg-white rounded-2xl p-6 shadow-sm mb-6">
            <h2 className="text-xs font-bold text-[#6C5CE7] tracking-wider mb-4 pb-2 border-b-2 border-[#ede9fe]">대화 로그</h2>
            <div className="space-y-4">
              {chatPairs.map((pair, i) => (
                <div key={i} className="pb-4 border-b border-gray-100 last:border-0 last:pb-0">
                  {pair.ai && (
                    <>
                      <p className="text-[10px] font-bold text-gray-300 uppercase tracking-wider mb-1">AI</p>
                      <div className="bg-[#f0edfc] rounded-xl rounded-bl-sm px-4 py-3 text-[13px] text-[#3a2f6e] leading-relaxed mb-2 max-w-[90%]">
                        {pair.ai}
                      </div>
                    </>
                  )}
                  <p className="text-[10px] font-bold text-gray-300 uppercase tracking-wider mb-1 text-right">참여자</p>
                  <div className="bg-[#6C5CE7] rounded-xl rounded-br-sm px-4 py-3 text-[13px] text-white leading-relaxed ml-auto max-w-[90%]">
                    {pair.user}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 푸터 */}
          <p className="text-center text-[11px] text-gray-300 mt-8 pb-8">
            RXR-AX-EDU · by Project Rent
          </p>
        </div>
      </div>
    );
  }

  // --- 목록 화면 ---
  const completed = sessions.filter(s => s.status === 'completed');
  const inProgress = sessions.filter(s => s.status !== 'completed');

  return (
    <div className="min-h-dvh bg-[#f4f3f8]">
      <div className="max-w-3xl mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <p className="text-xs font-bold tracking-wider text-[#6C5CE7] mb-1">RXR-AX-EDU</p>
          <h1 className="text-2xl font-extrabold text-gray-900 mb-1">관리자 대시보드</h1>
          <p className="text-sm text-gray-400">총 {sessions.length}건 · 완료 {completed.length}건</p>
        </div>

        {/* 완료된 세션 */}
        {completed.length > 0 && (
          <div className="mb-8">
            <h2 className="text-xs font-bold text-[#6C5CE7] tracking-wider mb-3">완료된 인터뷰</h2>
            <div className="space-y-3">
              {completed.map(s => (
                <button
                  key={s.id}
                  onClick={() => loadDetail(s.id)}
                  className="w-full bg-white rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow text-left flex items-center justify-between"
                >
                  <div>
                    <p className="font-bold text-gray-900 text-sm">{s.participant_name || '익명'}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{formatDate(s.started_at)} · {s.token}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold text-[#6C5CE7] bg-[#f2f0fe] px-2.5 py-1 rounded-full">완료</span>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#999" strokeWidth="2"><path d="M9 18l6-6-6-6"/></svg>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* 진행중 세션 */}
        {inProgress.length > 0 && (
          <div>
            <h2 className="text-xs font-bold text-gray-400 tracking-wider mb-3">진행중 / 미완료</h2>
            <div className="space-y-3">
              {inProgress.map(s => (
                <div
                  key={s.id}
                  className="w-full bg-white/60 rounded-xl p-4 text-left flex items-center justify-between"
                >
                  <div>
                    <p className="font-bold text-gray-600 text-sm">{s.participant_name || '(이름 미입력)'}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{formatDate(s.started_at)} · {s.token}</p>
                  </div>
                  <span className="text-[10px] font-bold text-gray-400 bg-gray-100 px-2.5 py-1 rounded-full">
                    {s.status === 'in_progress' ? `진행중 (Q${s.current_question})` : '시작'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {sessions.length === 0 && (
          <div className="text-center py-16 text-sm text-gray-400">아직 인터뷰가 없습니다.</div>
        )}
      </div>
    </div>
  );
}
