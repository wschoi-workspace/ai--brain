import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

export async function POST(req: NextRequest) {
  const { sessionId, questionId, rawAnswer, selectedOptions, isFollowUp, turnIndex, role } = await req.json();

  if (!sessionId) {
    return NextResponse.json({ error: 'sessionId required' }, { status: 400 });
  }

  // 대화형 모드: 턴 단위 저장
  if (typeof turnIndex === 'number') {
    const chatQuestionId = `turn_${turnIndex}`;

    await supabase.from('interview_answers').insert({
      session_id: sessionId,
      question_id: chatQuestionId,
      raw_answer: rawAnswer || '',
      selected_options: [],
      is_follow_up: role === 'assistant',
    });

    // 세션 진행 상태 업데이트
    await supabase
      .from('interview_sessions')
      .update({ current_question: turnIndex, status: 'in_progress' })
      .eq('id', sessionId);

    return NextResponse.json({ ok: true });
  }

  // 레거시 선택형 모드 (하위 호환)
  if (!questionId) {
    return NextResponse.json({ error: 'questionId required' }, { status: 400 });
  }

  const { data: existing } = await supabase
    .from('interview_answers')
    .select('id')
    .eq('session_id', sessionId)
    .eq('question_id', questionId)
    .single();

  if (existing) {
    await supabase
      .from('interview_answers')
      .update({ raw_answer: rawAnswer || '', selected_options: selectedOptions || [], is_follow_up: isFollowUp || false })
      .eq('id', existing.id);
  } else {
    await supabase.from('interview_answers').insert({
      session_id: sessionId,
      question_id: questionId,
      raw_answer: rawAnswer || '',
      selected_options: selectedOptions || [],
      is_follow_up: isFollowUp || false,
    });
  }

  const qNum = questionId === 'additional' ? 9 : parseInt(questionId.replace('q', ''));
  await supabase
    .from('interview_sessions')
    .update({ current_question: qNum, status: 'in_progress' })
    .eq('id', sessionId);

  return NextResponse.json({ ok: true });
}
