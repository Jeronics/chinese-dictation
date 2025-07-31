-- Drop the table if it exists (for a clean start)
drop table if exists public.daily_work_registry cascade;

-- 1. Table definition
create table if not exists public.daily_work_registry (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null,
    session_date date not null,
    session_type text not null, -- 'practice' or 'story'
    sentences_above_7 integer not null default 0,
    total_sentences integer not null default 0,
    story_id text, -- NULL for practice sessions
    story_parts_completed integer default 0, -- For story sessions, count parts completed
    created_at timestamp with time zone default now(),
    updated_at timestamp with time zone default now(),
    unique(user_id, session_date, session_type, story_id)
);

create index if not exists idx_daily_work_user_date on daily_work_registry(user_id, session_date);
create index if not exists idx_daily_work_user_type on daily_work_registry(user_id, session_type);

-- 2. RLS
alter table daily_work_registry enable row level security;

-- 3. Policies (with UUID cast)
drop policy if exists "Users can insert their own daily work" on daily_work_registry;
drop policy if exists "Users can update their own daily work" on daily_work_registry;
drop policy if exists "Users can select their own daily work" on daily_work_registry;
drop policy if exists "Users can delete their own daily work" on daily_work_registry;

create policy "Users can insert their own daily work"
on daily_work_registry
for insert
with check (user_id = auth.uid()::uuid);

create policy "Users can update their own daily work"
on daily_work_registry
for update
using (user_id = auth.uid()::uuid)
with check (user_id = auth.uid()::uuid);

create policy "Users can select their own daily work"
on daily_work_registry
for select
using (user_id = auth.uid()::uuid);

create policy "Users can delete their own daily work"
on daily_work_registry
for delete
using (user_id = auth.uid()::uuid);

comment on table daily_work_registry is 'Stores daily work registry and streak tracking for users';

-- 4. Trigger for updated_at
create or replace function update_updated_at_column()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists set_updated_at on public.daily_work_registry;

create trigger set_updated_at
before update on public.daily_work_registry
for each row
execute procedure update_updated_at_column(); 