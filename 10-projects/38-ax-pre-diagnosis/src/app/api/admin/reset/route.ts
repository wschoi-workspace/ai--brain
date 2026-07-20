import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

export async function POST(req: NextRequest) {
  const { code } = await req.json();
  if (code !== process.env.ADMIN_CODE) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 });
  }

  // 모든 세션 ID 가져오기
  const { data: sessions } = await supabase
    .from('interview_sessions')
    .select('id');

  if (!sessions || sessions.length === 0) {
    return NextResponse.json({ message: 'no sessions to delete', deleted: 0 });
  }

  const ids = sessions.map(s => s.id);

  // 순서대로 삭제: answers → analysis → sessions
  for (const id of ids) {
    await supabase.from('interview_answers').delete().eq('session_id', id);
    await supabase.from('interview_analysis').delete().eq('session_id', id);
  }

  for (const id of ids) {
    await supabase.from('interview_sessions').delete().eq('id', id);
  }

  return NextResponse.json({ message: 'all data cleared', deleted: ids.length });
}
