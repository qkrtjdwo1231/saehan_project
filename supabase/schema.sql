create table if not exists documents (
  key text primary key,
  data jsonb not null,
  updated_at timestamptz default now()
);

create table if not exists inventory (
  item_type text primary key,
  qty numeric not null default 0,
  updated_by text,
  updated_at timestamptz default now()
);

create table if not exists plan_versions (
  id bigserial primary key,
  week_start date not null,
  name text,
  published_at timestamptz,
  published_by text
);

create table if not exists plan_cells (
  id bigserial primary key,
  week_start date not null,
  machine text not null,
  day int not null,
  item_type text not null,
  qty numeric not null default 0,
  updated_by text,
  updated_at timestamptz default now(),
  unique (week_start, machine, day, item_type)
);

create table if not exists plan_changes (
  id bigserial primary key,
  ts timestamptz default now(),
  week_start date not null,
  user_name text,
  machine text,
  day int,
  item_type text,
  qty_before numeric,
  qty_after numeric,
  reason text,
  memo text
);

alter table documents disable row level security;
alter table inventory disable row level security;
alter table plan_versions disable row level security;
alter table plan_cells disable row level security;
alter table plan_changes disable row level security;
