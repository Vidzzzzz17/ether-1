create extension if not exists pgcrypto;

create table if not exists public.conversations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null default 'New conversation',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('user', 'assistant')),
  content text not null default '',
  artifacts jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists messages_conversation_created_idx on public.messages(conversation_id, created_at);
create index if not exists conversations_user_updated_idx on public.conversations(user_id, updated_at desc);

alter table public.conversations enable row level security;
alter table public.messages enable row level security;

create policy "Users manage own conversations" on public.conversations
  for all to authenticated using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

create policy "Users read own conversation messages" on public.messages
  for select to authenticated using ((select auth.uid()) = user_id);
create policy "Users add own messages" on public.messages
  for insert to authenticated with check (
    (select auth.uid()) = user_id and exists (
      select 1 from public.conversations c where c.id = conversation_id and c.user_id = (select auth.uid())
    )
  );
create policy "Users update own messages" on public.messages
  for update to authenticated using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);
create policy "Users delete own messages" on public.messages
  for delete to authenticated using ((select auth.uid()) = user_id);

grant select, insert, update, delete on public.conversations to authenticated;
grant select, insert, update, delete on public.messages to authenticated;

