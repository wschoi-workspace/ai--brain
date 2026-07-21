'use client';

import { useParams, useRouter } from 'next/navigation';
import { useState } from 'react';

export default function JoinPage() {
  const { code } = useParams<{ code: string }>();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleStart() {
    setLoading(true);
    setError('');
    try {
      const res = await fetch('/api/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ educationCode: code, count: 1 }),
      });
      if (!res.ok) {
        setError('유효하지 않은 교육 코드입니다.');
        setLoading(false);
        return;
      }
      const data = await res.json();
      if (data.tokens && data.tokens.length > 0) {
        router.push(`/interview/${data.tokens[0]}`);
      }
    } catch {
      setError('오류가 발생했습니다. 다시 시도해 주세요.');
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-dvh bg-[#f7f7fb] px-6">
      <div className="text-center max-w-sm">
        <p className="text-xs font-bold tracking-wider text-[#6C5CE7] mb-3">RXR-AX-EDU</p>
        <h1 className="text-2xl font-extrabold text-gray-900 mb-2">AX 교육 사전진단</h1>
        <p className="text-sm text-gray-500 leading-relaxed mb-8">
          교육 전 간단한 인터뷰입니다.<br />약 5~7분 소요되며, 답변은 교육 설계에 활용됩니다.
        </p>
        <button
          onClick={handleStart}
          disabled={loading}
          className={`w-full py-3.5 rounded-xl font-bold text-sm transition-colors ${
            loading
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-[#6C5CE7] text-white hover:bg-[#5a4bd6]'
          }`}
        >
          {loading ? '준비 중...' : '시작하기'}
        </button>
        {error && <p className="text-sm text-red-500 mt-3">{error}</p>}
      </div>
    </div>
  );
}
