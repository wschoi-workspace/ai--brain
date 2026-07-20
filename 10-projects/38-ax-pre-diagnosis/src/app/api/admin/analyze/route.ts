import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';
import { createClient } from '@supabase/supabase-js';

function getOpenAI() {
  return new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
}

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

const DESIRE_ANALYSIS_PROMPT = `너는 AX 교육 사전진단 인터뷰 데이터를 분석하는 조직심리·교육설계 전문가다.

참여자의 대화 전문을 읽고, 다음 두 가지를 JSON으로 반환한다:

## 1. confirmed_summary (합의된 최종 의견)
인터뷰 마지막에 참여자가 "맞다"고 확인한 7가지 항목 요약.
각 항목은 참여자의 원문 표현을 최대한 보존하되, 한 문장으로 정리한다.
반드시 아래 키명을 사용한다:
- ai_usage_level: AI 사용 수준
- participation_reason: 참여 이유
- expected_change: 기대하는 변화
- target_task: 적용 업무
- ai_role_level: AI 역할 수준
- satisfaction_criteria: 만족 기준
- first_action: 첫 행동

## 2. desire_analysis (희망·욕구 심층 분석)
참여자의 답변에서 드러나는 깊은 욕구와 기대를 분석한다:

- underlying_desire: 표면적 요청 아래 숨은 진짜 욕구 (1~2문장)
- frustration_source: 현재 불만·고통의 근원 (구체적으로)
- ideal_future_state: 참여자가 그리는 이상적 업무 모습
- gap_analysis: 현재 상태와 이상 상태 사이의 간극
- motivation_type: 동기 유형 (성장형/효율형/불안형/호기심형 중 택1 + 근거)
- readiness_level: 변화 준비도 (1~5, 5가 가장 높음) + 근거
- education_leverage_points: 이 참여자에게 교육이 최대 효과를 낼 수 있는 지점 (2~3개)
- risk_factors: 교육 효과를 떨어뜨릴 수 있는 위험 요소 (기대 과잉, 시간 부족 등)
- personalized_recommendation: 이 참여자만을 위한 맞춤 교육 제안 (구체적으로)

## 3. additional_opinions (추가 의견)
참여자가 마지막에 별도로 남긴 추가 의견이나 기대치. 없으면 null.

분석 원칙:
- 참여자의 실제 발언을 근거로 분석한다. 추측은 최소화.
- "~라고 말했다" 형태로 근거를 명시한다.
- 교육 설계자가 바로 활용할 수 있는 수준으로 구체적으로 작성한다.`;

export async function POST(req: NextRequest) {
  const { code, sessionId } = await req.json();
  if (code !== process.env.ADMIN_CODE) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 });
  }

  // 대화 로그 가져오기
  const { data: answers } = await supabase
    .from('interview_answers')
    .select('*')
    .eq('session_id', sessionId)
    .order('created_at', { ascending: true });

  if (!answers || answers.length === 0) {
    return NextResponse.json({ error: 'no answers found' }, { status: 404 });
  }

  // 대화 텍스트 재구성
  const conversationText = answers
    .map(a => `${a.is_follow_up ? '인터뷰어' : '참여자'}: ${a.raw_answer}`)
    .join('\n\n');

  try {
    const completion = await getOpenAI().chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        { role: 'system', content: DESIRE_ANALYSIS_PROMPT },
        { role: 'user', content: `다음은 참여자의 인터뷰 대화 전문입니다:\n\n${conversationText}` },
      ],
      response_format: { type: 'json_object' },
      temperature: 0.3,
    });

    const analysis = JSON.parse(completion.choices[0].message.content || '{}');
    return NextResponse.json(analysis);
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : 'unknown error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
