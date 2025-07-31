-- Drop the table if it exists (clean start)
drop table if exists public.character_progress cascade;

-- 1. Table
create table if not exists public.character_progress (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null,
    hanzi text not null,
    hsk_level int,
    grade int not null default -1,
    last_seen timestamp with time zone default now(),
    inserted_at timestamp with time zone default now(),
    updated_at timestamp with time zone default now()
);

create unique index if not exists character_progress_user_hanzi_idx
    on public.character_progress (user_id, hanzi);

-- 2. RLS
alter table public.character_progress enable row level security;

-- 3. Policies (with UUID cast)
create policy "Allow user to read own character progress"
on public.character_progress
for select
using (user_id = auth.uid()::uuid);

create policy "Allow user to insert own character progress"
on public.character_progress
for insert
with check (user_id = auth.uid()::uuid);

create policy "Allow user to update own character progress"
on public.character_progress
for update
using (user_id = auth.uid()::uuid);

create policy "Allow user to delete own character progress"
on public.character_progress
for delete
using (user_id = auth.uid()::uuid);

create policy "Allow service key full access"
on public.character_progress
for all
using (auth.role() = 'service_role' or user_id = auth.uid()::uuid)
with check (auth.role() = 'service_role' or user_id = auth.uid()::uuid);

-- 4. Trigger for updated_at
create or replace function update_updated_at_column()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists set_updated_at on public.character_progress;

create trigger set_updated_at
before update on public.character_progress
for each row
execute procedure update_updated_at_column();