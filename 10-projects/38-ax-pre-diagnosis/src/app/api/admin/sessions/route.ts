import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

export async function GET(req: NextRequest) {
  const code = req.nextUrl.searchParams.get('code');
  if (code !== process.env.ADMIN_CODE) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 });
  }

  const sessionId = req.nextUrl.searchParams.get('id');

  // 단건 조회
  if (sessionId) {
    const { data: session } = await supabase
      .from('interview_sessions')
      .select('*, interview_answers(*)')
      .eq('id', sessionId)
      .single();

    if (!session) return NextResponse.json({ error: 'not found' }, { status: 404 });

    const { data: analysis } = await supabase
      .from('interview_analysis')
      .select('*')
      .eq('session_id', sessionId)
      .single();

    return NextResponse.json({ session, analysis });
  }

  // 목록 조회
  const { data: sessions } = await supabase
    .from('interview_sessions')
    .select('id, token, participant_name, status, started_at, completed_at, current_question')
    .order('started_at', { ascending: false });

  return NextResponse.json({ sessions: sessions || [] });
}
