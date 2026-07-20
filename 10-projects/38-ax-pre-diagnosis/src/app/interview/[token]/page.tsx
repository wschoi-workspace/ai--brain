'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams } from 'next/navigation';
import type { AnalysisResult } from '@/lib/types';

type Phase = 'loading' | 'welcome' | 'consent' | 'name' | 'conversation' | 'analyzing' | 'summary' | 'done' | 'error';

interface ChatMsg {
  role: 'bot' | 'user';
  content: string;
}

export default function InterviewPage() {
  const { token } = useParams<{ token: string }>();
  const [phase, setPhase] = useState<Phase>('loading');
  const [session, setSession] = useState<{ id: string; participant_name: string | null } | null>(null);
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [chatHistory, setChatHistory] = useState<{ role: 'assistant' | 'user'; content: string }[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [progress, setProgress] = useState(0);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [turnIndex, setTurnIndex] = useState(0);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
  }, []);

  // 세션 로드
  useEffect(() => {
    if (!token) return;
    fetch(`/api/session?token=${token}`)
      .then(r => r.ok ? r.json() : Promise.reject())
      .then(data => {
        setSession({ id: data.id, participant_name: data.participant_name });
        if (data.status === 'completed') {
          setPhase('done');
        } else {
          setPhase('welcome');
        }
      })
      .catch(() => setPhase('error'));
  }, [token]);

  useEffect(scrollToBottom, [messages, scrollToBottom]);

  function addMsg(msg: ChatMsg) {
    setMessages(prev => [...prev, msg]);
  }

  function handleConsent() {
    fetch('/api/session', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, consent_given: true }),
    });
    setPhase('name');
    addMsg({ role: 'bot', content: '이름을 알려주세요. 익명으로 참여하셔도 됩니다.' });
  }

  async function handleName() {
    const name = inputValue.trim() || '익명';
    fetch('/api/session', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, participant_name: name }),
    });
    setSession(prev => prev ? { ...prev, participant_name: name } : prev);
    addMsg({ role: 'user', content: name });
    setInputValue('');

    setPhase('conversation');

    // AI에게 첫 대화 시작 요청
    const initialHistory: { role: 'assistant' | 'user'; content: string }[] = [
      { role: 'user', content: `[시스템: 참여자 "${name}"이(가) 인터뷰를 시작합니다. 첫 인사와 함께 자연스럽게 첫 번째 질문을 해주세요. 약 5~7분이면 끝나는 짧은 대화임을 알려주세요.]` },
    ];

    await sendToAI(initialHistory, name);
  }

  async function sendToAI(history: { role: 'assistant' | 'user'; content: string }[], name?: string) {
    setIsTyping(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: history,
          participantName: name || session?.participant_name,
        }),
      });

      if (!res.ok) throw new Error('API error');
      const data = await res.json();

      const aiMessage = data.message;
      const newProgress = data.progress || 0;
      const isComplete = data.isComplete === true;

      // 채팅에 AI 응답 추가
      addMsg({ role: 'bot', content: aiMessage });
      setProgress(newProgress);

      // 히스토리 업데이트
      const updatedHistory = [...history, { role: 'assistant' as const, content: aiMessage }];
      setChatHistory(updatedHistory);

      // 대화 턴 저장
      const newTurn = turnIndex + 1;
      setTurnIndex(newTurn);
      saveTurn(newTurn, aiMessage, 'assistant');

      if (isComplete) {
        // 대화 완료 → 분석 시작
        setTimeout(() => startAnalysis(updatedHistory), 500);
      }
    } catch {
      addMsg({ role: 'bot', content: '죄송합니다, 일시적인 오류가 발생했습니다. 다시 입력해 주세요.' });
    } finally {
      setIsTyping(false);
    }
  }

  async function handleUserSubmit() {
    const text = inputValue.trim();
    if (!text || isTyping) return;

    addMsg({ role: 'user', content: text });
    setInputValue('');

    // 턴 저장
    const newTurn = turnIndex + 1;
    setTurnIndex(newTurn);
    saveTurn(newTurn, text, 'user');

    // AI에 전송
    const updatedHistory = [...chatHistory, { role: 'user' as const, content: text }];
    setChatHistory(updatedHistory);
    await sendToAI(updatedHistory);
  }

  function saveTurn(turn: number, content: string, role: string) {
    fetch('/api/answer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sessionId: session?.id,
        turnIndex: turn,
        rawAnswer: content,
        role,
      }),
    });
  }

  async function startAnalysis(history: { role: 'assistant' | 'user'; content: string }[]) {
    setPhase('analyzing');
    addMsg({ role: 'bot', content: '답변해 주신 내용을 정리하고 있습니다...' });

    // 대화 전체를 텍스트로 변환
    const conversationText = history
      .filter(m => !m.content.startsWith('[시스템:'))
      .map(m => `${m.role === 'user' ? '참여자' : '인터뷰어'}: ${m.content}`)
      .join('\n\n');

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers: conversationText, sessionId: session?.id }),
      });
      const result = await res.json();
      setAnalysis(result);
      setPhase('summary');
    } catch {
      addMsg({ role: 'bot', content: '분석 중 오류가 발생했습니다. 답변은 저장되었습니다.' });
      setPhase('done');
    }
  }

  function handleConfirmSummary() {
    setPhase('done');
    addMsg({ role: 'bot', content: '감사합니다! 답변은 교육 설계에 소중하게 반영하겠습니다.' });
  }

  // 음성 입력
  function toggleVoice() {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const W = window as any;
    const SR = W.SpeechRecognition || W.webkitSpeechRecognition;
    if (!SR) {
      alert('이 브라우저에서는 음성 입력을 지원하지 않습니다.');
      return;
    }
    if (isListening) {
      setIsListening(false);
      return;
    }
    const recognition = new SR();
    recognition.lang = 'ko-KR';
    recognition.interimResults = false;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    recognition.onresult = (e: any) => {
      const text = e.results[0][0].transcript;
      setInputValue((prev: string) => prev + text);
    };
    recognition.onend = () => setIsListening(false);
    recognition.start();
    setIsListening(true);
  }

  const showInput = phase === 'name' || phase === 'conversation';
  const progressPercent = phase === 'analyzing' || phase === 'summary' || phase === 'done' ? 100 : progress;

  return (
    <div className="flex flex-col h-dvh max-w-lg mx-auto bg-white">
      {/* 헤더 */}
      <header className="flex-none px-5 py-4 border-b border-gray-100 bg-white">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-bold tracking-wider text-[#6C5CE7]">AX 교육 사전진단</p>
            <p className="text-sm text-gray-500 mt-0.5">RXR-AX-EDU</p>
          </div>
          {phase !== 'loading' && phase !== 'welcome' && phase !== 'error' && (
            <div className="text-xs text-gray-400 font-medium">{progressPercent}%</div>
          )}
        </div>
        {phase !== 'loading' && phase !== 'welcome' && phase !== 'error' && (
          <div className="mt-3 h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-[#6C5CE7] rounded-full transition-all duration-700"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        )}
      </header>

      {/* 채팅 영역 */}
      <main className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
        {phase === 'loading' && (
          <div className="flex items-center justify-center h-full">
            <div className="animate-pulse text-gray-400">불러오는 중...</div>
          </div>
        )}

        {phase === 'error' && (
          <div className="flex items-center justify-center h-full text-center">
            <div>
              <p className="text-lg font-bold text-gray-800 mb-2">유효하지 않은 링크입니다</p>
              <p className="text-sm text-gray-500">교육 담당자에게 새 링크를 요청해 주세요.</p>
            </div>
          </div>
        )}

        {phase === 'welcome' && (
          <div className="space-y-4">
            <div className="bg-[#f2f0fe] rounded-2xl p-5">
              <p className="font-bold text-[#6C5CE7] text-sm mb-3">안녕하세요!</p>
              <p className="text-sm leading-relaxed text-gray-700">
                이번 대화는 AX 교육을 준비하기 위해, 교육을 통해 어떤 도움과 변화를 기대하시는지 알아보는 짧은 사전 인터뷰입니다.
              </p>
              <p className="text-sm leading-relaxed text-gray-700 mt-3">
                AI를 잘 모르셔도 전혀 문제가 없습니다. 전문적인 용어나 정답은 필요하지 않습니다.
              </p>
              <p className="text-sm leading-relaxed text-gray-700 mt-3">
                약 <strong>5~7분</strong> 정도 소요되며, 답변은 교육의 수준과 내용, 실습 사례를 구성하는 데 활용됩니다.
              </p>
              <p className="text-sm leading-relaxed text-gray-700 mt-3">
                타이핑 대신 <strong>마이크 버튼</strong>을 눌러 말로 답하셔도 됩니다.
              </p>
            </div>
            <div className="bg-gray-50 rounded-xl p-4 text-xs text-gray-500 space-y-1.5">
              <p>* 답변은 교육 기획 목적으로만 활용됩니다.</p>
              <p>* 민감한 회사 정보나 개인정보는 입력하지 않도록 안내드립니다.</p>
            </div>
            <button
              onClick={handleConsent}
              className="w-full py-3.5 bg-[#6C5CE7] text-white rounded-xl font-bold text-sm hover:bg-[#5a4bd6] transition-colors"
            >
              동의하고 시작하기
            </button>
          </div>
        )}

        {/* 채팅 메시지 */}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                msg.role === 'user'
                  ? 'bg-[#6C5CE7] text-white rounded-br-md'
                  : 'bg-gray-100 text-gray-800 rounded-bl-md'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {/* 타이핑 인디케이터 */}
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-3 flex items-center gap-1">
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        )}

        {/* 분석 중 */}
        {phase === 'analyzing' && (
          <div className="flex justify-center py-4">
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              분석 중...
            </div>
          </div>
        )}

        {/* 요약 */}
        {phase === 'summary' && analysis && (
          <div className="space-y-4">
            <div className="bg-[#f2f0fe] rounded-2xl p-5">
              <p className="font-bold text-[#6C5CE7] text-sm mb-4">답변해 주신 내용을 다음과 같이 이해했습니다.</p>
              <div className="space-y-3 text-sm text-gray-700">
                <div>
                  <p className="font-bold text-gray-500 text-xs mb-1">이번 교육에서 가장 기대하는 변화</p>
                  <p>{analysis.primary_expectation}</p>
                </div>
                <div>
                  <p className="font-bold text-gray-500 text-xs mb-1">가장 먼저 적용하고 싶은 업무</p>
                  <p>{analysis.target_task}</p>
                </div>
                <div>
                  <p className="font-bold text-gray-500 text-xs mb-1">기대하는 AI의 역할</p>
                  <p>{analysis.desired_ai_role}</p>
                </div>
                <div>
                  <p className="font-bold text-gray-500 text-xs mb-1">교육 후 가장 먼저 해보고 싶은 일</p>
                  <p>{analysis.first_action}</p>
                </div>
                {analysis.participant_summary && (
                  <div>
                    <p className="font-bold text-gray-500 text-xs mb-1">추천 교육 방향</p>
                    <p>{analysis.participant_summary}</p>
                  </div>
                )}
              </div>
            </div>
            <p className="text-sm text-gray-600 text-center">제가 이해한 내용이 맞나요?</p>
            <div className="flex gap-3">
              <button
                onClick={handleConfirmSummary}
                className="flex-1 py-3 bg-[#6C5CE7] text-white rounded-xl font-bold text-sm"
              >
                네, 맞습니다
              </button>
              <button
                onClick={handleConfirmSummary}
                className="flex-1 py-3 bg-gray-100 text-gray-600 rounded-xl font-bold text-sm"
              >
                괜찮습니다
              </button>
            </div>
          </div>
        )}

        {/* 완료 */}
        {phase === 'done' && (
          <div className="flex items-center justify-center h-32">
            <div className="text-center">
              <p className="text-2xl mb-2">&#10003;</p>
              <p className="text-sm text-gray-500">인터뷰가 완료되었습니다. 감사합니다!</p>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </main>

      {/* 입력 영역 */}
      {showInput && (
        <footer className="flex-none border-t border-gray-100 bg-white px-4 py-3">
          <div className="flex items-end gap-2">
            <button
              onClick={toggleVoice}
              className={`flex-none w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
                isListening ? 'bg-red-500 text-white animate-pulse' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
              }`}
              title="음성 입력"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="22" />
              </svg>
            </button>
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={e => setInputValue(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  if (phase === 'name') handleName();
                  else handleUserSubmit();
                }
              }}
              placeholder={phase === 'name' ? '이름 입력 (또는 빈칸으로 익명)' : '답변을 입력하세요...'}
              className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 text-sm resize-none focus:outline-none focus:border-[#6C5CE7] max-h-24"
              rows={1}
              disabled={isTyping}
            />
            <button
              onClick={() => phase === 'name' ? handleName() : handleUserSubmit()}
              disabled={isTyping}
              className={`flex-none w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
                isTyping ? 'bg-gray-300 text-gray-500 cursor-not-allowed' : 'bg-[#6C5CE7] text-white hover:bg-[#5a4bd6]'
              }`}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
        </footer>
      )}
    </div>
  );
}
