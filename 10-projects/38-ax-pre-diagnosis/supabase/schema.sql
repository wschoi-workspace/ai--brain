-- AX 사전진단 챗봇 DB 스키마

-- 교육 세션 (교육 프로그램 단위)
create table if not exists education_sessions (
  id uuid primary key default gen_random_uuid(),
  code text not null unique,           -- 'RXR_AX_EDU'
  title text not null,                 -- 'AX 초심자 교육'
  created_at timestamptz default now()
);

-- 인터뷰 세션 (참여자별)
create table if not exists interview_sessions (
  id uuid primary key default gen_random_uuid(),
  education_id uuid references education_sessions(id),
  token text not null unique,          -- URL 토큰
  participant_name text,
  status text default 'started' check (status in ('started','in_progress','completed')),
  current_question int default 0,
  consent_given boolean default false,
  started_at timestamptz default now(),
  completed_at timestamptz
);

-- 개별 답변
create table if not exists interview_answers (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references interview_sessions(id) on delete cascade,
  question_id text not null,           -- 'q1', 'q2', ... 'q8', 'additional'
  raw_answer text,
  selected_options text[],
  is_follow_up boolean default false,
  created_at timestamptz default now()
);

-- AI 분석 결과
create table if not exists interview_analysis (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references interview_sessions(id) on delete cascade unique,
  ai_familiarity_level int,
  participation_reason text,
  primary_expectation text,
  secondary_expectations text[],
  target_task text,
  pain_point text,
  desired_ai_role text,
  expected_completion_level int,
  success_criteria text[],
  first_action text,
  expectation_clarity_score int,
  recommended_difficulty text,
  recommended_topics text[],
  recommended_practice text,
  needs_expectation_adjustment boolean default false,
  raw_analysis jsonb,
  created_at timestamptz default now()
);

-- RLS 정책
alter table education_sessions enable row level security;
alter table interview_sessions enable row level security;
alter table interview_answers enable row level security;
alter table interview_analysis enable row level security;

-- anon 사용자 접근 정책 (토큰 기반)
create policy "anon_read_education" on education_sessions for select to anon using (true);
create policy "anon_read_session" on interview_sessions for select to anon using (true);
create policy "anon_update_session" on interview_sessions for update to anon using (true);
create policy "anon_insert_answer" on interview_answers for insert to anon with check (true);
create policy "anon_read_answer" on interview_answers for select to anon using (true);
create policy "anon_insert_analysis" on interview_analysis for insert to anon with check (true);
create policy "anon_read_analysis" on interview_analysis for select to anon using (true);

-- 첫 교육 세션 생성
insert into education_sessions (code, title) values ('RXR_AX_EDU', 'AX 초심자 교육')
on conflict (code) do nothing;
