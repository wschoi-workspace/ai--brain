import { Answer, AnalysisResult } from './types';

const SYSTEM_PROMPT = `너는 AX 교육 사전진단 데이터를 분석하는 전문가다.
참여자의 인터뷰 답변을 받아 구조화된 분석 결과를 JSON으로 반환한다.

분석 원칙:
- 사용자의 원문 표현을 최대한 보존한다
- AI의 추론과 사용자의 직접 발언을 구분한다
- 기대가 과도하면 needs_expectation_adjustment를 true로 표시한다
- 기대 구체성 점수는 7개 항목(각 0~2점, 총 14점)으로 평가한다

기대 구체성 채점 기준:
1. 기대하는 변화가 특정되었는가 (0~2)
2. 적용하고 싶은 업무가 특정되었는가 (0~2)
3. 현재 불편이 설명되었는가 (0~2)
4. 기대하는 AI 역할이 특정되었는가 (0~2)
5. 기대 완성도가 특정되었는가 (0~2)
6. 성공 기준이 특정되었는가 (0~2)
7. 교육 후 행동이 특정되었는가 (0~2)

난이도 분류:
- beginner_concept: AI 기본 개념 설명 필요
- beginner_practical: 간단한 실습 위주
- intermediate: 실제 업무 적용
- advanced: 반복 활용 및 워크플로 설계`;

export async function analyzeInterview(answers: Answer[]): Promise<AnalysisResult> {
  const answersText = answers.map(a => {
    const selected = a.selectedOptions.length > 0 ? `선택: ${a.selectedOptions.join(', ')}` : '';
    const raw = a.rawAnswer ? `답변: ${a.rawAnswer}` : '';
    return `[${a.questionId}] ${selected} ${raw}`.trim();
  }).join('\n');

  const res = await fetch('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ answers: answersText }),
  });

  if (!res.ok) throw new Error('분석 실패');
  return res.json();
}
