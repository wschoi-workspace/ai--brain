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

const SYSTEM_PROMPT = `너는 AX 교육 사전진단 데이터를 분석하는 전문가다.
참여자의 인터뷰 답변을 받아 구조화된 분석 결과를 JSON으로 반환한다.

분석 원칙:
- 사용자의 원문 표현을 최대한 보존한다
- 기대가 과도하면 needs_expectation_adjustment를 true로 표시한다

기대 구체성 채점 (7항목, 각 0~2점, 총 14점):
1. 기대하는 변화 특정 여부
2. 적용 업무 특정 여부
3. 현재 불편 설명 여부
4. 기대 AI 역할 특정 여부
5. 기대 완성도 특정 여부
6. 성공 기준 특정 여부
7. 교육 후 행동 특정 여부

점수 분류:
- 0~3: 기대 미형성
- 4~6: 막연한 기대
- 7~9: 활용 방향 형성
- 10~12: 구체적 활용 기대
- 13~14: 명확한 실행 목표

난이도 분류:
- beginner_concept: AI 기본 개념 설명 필요
- beginner_practical: 간단한 실습 위주
- intermediate: 실제 업무 적용
- advanced: 반복 활용 및 워크플로 설계

반드시 아래 JSON 스키마로 응답하라.`;

const RESPONSE_SCHEMA = {
  type: "object" as const,
  additionalProperties: false,
  properties: {
    ai_familiarity_level: { type: "number" as const },
    participation_reason: { type: "string" as const },
    primary_expectation: { type: "string" as const },
    secondary_expectations: { type: "array" as const, items: { type: "string" as const } },
    target_task: { type: "string" as const },
    pain_point: { type: "string" as const },
    desired_ai_role: { type: "string" as const },
    expected_completion_level: { type: "number" as const },
    success_criteria: { type: "array" as const, items: { type: "string" as const } },
    first_action: { type: "string" as const },
    expectation_clarity_score: { type: "number" as const },
    recommended_difficulty: { type: "string" as const },
    recommended_topics: { type: "array" as const, items: { type: "string" as const } },
    recommended_practice: { type: "string" as const },
    needs_expectation_adjustment: { type: "boolean" as const },
    participant_summary: { type: "string" as const },
  },
  required: [
    "ai_familiarity_level", "participation_reason", "primary_expectation",
    "secondary_expectations", "target_task", "pain_point", "desired_ai_role",
    "expected_completion_level", "success_criteria", "first_action",
    "expectation_clarity_score", "recommended_difficulty", "recommended_topics",
    "recommended_practice", "needs_expectation_adjustment", "participant_summary"
  ],
};

export async function POST(req: NextRequest) {
  const { answers, sessionId } = await req.json();

  try {
    const completion = await getOpenAI().chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: `다음은 참여자의 인터뷰 답변입니다:\n\n${answers}` },
      ],
      response_format: {
        type: 'json_schema',
        json_schema: {
          name: 'interview_analysis',
          schema: RESPONSE_SCHEMA,
          strict: true,
        },
      },
      temperature: 0.3,
    });

    const analysis = JSON.parse(completion.choices[0].message.content || '{}');

    // DB 저장
    if (sessionId) {
      await supabase.from('interview_analysis').upsert({
        session_id: sessionId,
        ...analysis,
        raw_analysis: analysis,
      }, { onConflict: 'session_id' });

      await supabase
        .from('interview_sessions')
        .update({ status: 'completed', completed_at: new Date().toISOString() })
        .eq('id', sessionId);
    }

    return NextResponse.json(analysis);
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : 'unknown error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
