create extension if not exists pgcrypto;
create extension if not exists vector;

create table if not exists candidates (
  id uuid primary key default gen_random_uuid(),
  full_name text,
  headline text,
  summary text,
  created_at timestamptz not null default now()
);

create table if not exists resumes (
  id uuid primary key default gen_random_uuid(),
  candidate_id uuid references candidates(id) on delete cascade,
  storage_path text not null,
  raw_filename text not null,
  parsed_json jsonb not null,
  created_at timestamptz not null default now()
);

create table if not exists resume_sections (
  id uuid primary key default gen_random_uuid(),
  resume_id uuid references resumes(id) on delete cascade,
  section_type text not null,
  content text not null,
  metadata jsonb not null default '{}'::jsonb
);

create table if not exists interviews (
  id uuid primary key default gen_random_uuid(),
  access_token_hash text,
  candidate_id uuid references candidates(id) on delete cascade,
  resume_id uuid references resumes(id) on delete set null,
  target_company text,
  target_role text,
  current_phase text not null,
  hint_count integer not null default 0,
  hint_recovery_count integer not null default 0,
  empathy_prompt_count integer not null default 0,
  factual_question_count integer not null default 0,
  phase_scores jsonb not null default '{}'::jsonb,
  overall_score numeric(4, 1),
  final_feedback jsonb,
  realtime_mode_enabled boolean not null default false,
  video_mode_enabled boolean not null default false,
  proctoring_summary jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists interview_messages (
  id uuid primary key default gen_random_uuid(),
  interview_id uuid references interviews(id) on delete cascade,
  role text not null,
  phase text not null,
  message_text text not null,
  hint_used boolean not null default false,
  hint_recovery boolean not null default false,
  empathy_used boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists evaluations (
  id uuid primary key default gen_random_uuid(),
  interview_id uuid references interviews(id) on delete cascade,
  phase text not null,
  label text,
  score numeric(4, 1),
  rationale text,
  evidence jsonb not null default '[]'::jsonb,
  dimensions jsonb not null default '{}'::jsonb,
  strengths jsonb not null default '[]'::jsonb,
  weaknesses jsonb not null default '[]'::jsonb,
  suggestion text,
  confidence numeric(4, 2),
  created_at timestamptz not null default now()
);

create table if not exists question_bank (
  id uuid primary key default gen_random_uuid(),
  source text not null,
  domain text not null,
  question text not null,
  answer text,
  metadata jsonb not null default '{}'::jsonb,
  embedding vector(384),
  created_at timestamptz not null default now()
);

create index if not exists idx_question_bank_domain on question_bank(domain);

alter table question_bank
  add column if not exists source_ordinal integer,
  add column if not exists domain_tags text[] not null default '{}'::text[],
  add column if not exists embedding_provider text,
  add column if not exists embedding_model text,
  add column if not exists embedding_updated_at timestamptz;

create index if not exists idx_question_bank_domain_tags on question_bank using gin(domain_tags);
create index if not exists idx_question_bank_embedding on question_bank using hnsw (embedding vector_cosine_ops);

alter table interviews
  add column if not exists access_token_hash text,
  add column if not exists hint_recovery_count integer not null default 0,
  add column if not exists empathy_prompt_count integer not null default 0,
  add column if not exists final_feedback jsonb,
  add column if not exists realtime_mode_enabled boolean not null default false,
  add column if not exists video_mode_enabled boolean not null default false,
  add column if not exists proctoring_summary jsonb not null default '{}'::jsonb;

alter table interview_messages
  add column if not exists hint_used boolean not null default false,
  add column if not exists hint_recovery boolean not null default false,
  add column if not exists empathy_used boolean not null default false;

alter table evaluations
  add column if not exists label text,
  add column if not exists dimensions jsonb not null default '{}'::jsonb,
  add column if not exists strengths jsonb not null default '[]'::jsonb,
  add column if not exists weaknesses jsonb not null default '[]'::jsonb,
  add column if not exists suggestion text,
  add column if not exists confidence numeric(4, 2);

alter table candidates enable row level security;
alter table resumes enable row level security;
alter table resume_sections enable row level security;
alter table interviews enable row level security;
alter table interview_messages enable row level security;
alter table evaluations enable row level security;
alter table question_bank enable row level security;

drop policy if exists "service role manages candidates" on candidates;
create policy "service role manages candidates"
  on candidates
  for all
  to service_role
  using (true)
  with check (true);

drop policy if exists "service role manages resumes" on resumes;
create policy "service role manages resumes"
  on resumes
  for all
  to service_role
  using (true)
  with check (true);

drop policy if exists "service role manages resume sections" on resume_sections;
create policy "service role manages resume sections"
  on resume_sections
  for all
  to service_role
  using (true)
  with check (true);

drop policy if exists "service role manages interviews" on interviews;
create policy "service role manages interviews"
  on interviews
  for all
  to service_role
  using (true)
  with check (true);

drop policy if exists "service role manages interview messages" on interview_messages;
create policy "service role manages interview messages"
  on interview_messages
  for all
  to service_role
  using (true)
  with check (true);

drop policy if exists "service role manages evaluations" on evaluations;
create policy "service role manages evaluations"
  on evaluations
  for all
  to service_role
  using (true)
  with check (true);

drop policy if exists "service role manages question bank" on question_bank;
create policy "service role manages question bank"
  on question_bank
  for all
  to service_role
  using (true)
  with check (true);

drop policy if exists "service role manages resume bucket objects" on storage.objects;
create policy "service role manages resume bucket objects"
  on storage.objects
  for all
  to service_role
  using (bucket_id = 'resumes')
  with check (bucket_id = 'resumes');
