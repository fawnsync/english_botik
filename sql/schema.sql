create table if not exists public.users (
  user_id bigint primary key,
  username text,
  first_name text,
  created_at timestamptz not null default now()
);

create table if not exists public.words (
  id bigint generated always as identity primary key,
  user_id bigint not null references public.users(user_id) on delete cascade,
  source_word text not null,
  source_lang text not null check (source_lang in ('en', 'ru')),
  translated_word text not null,
  note text,
  created_at timestamptz not null default now()
);

create index if not exists words_user_id_created_at_idx
  on public.words(user_id, created_at desc);
