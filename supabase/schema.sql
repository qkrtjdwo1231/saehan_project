-- 새한프라텍 생산계획 웹 · 수파베이스 표 정의 (SQL Editor에 붙여 넣어 실행)
-- 시연용이라 RLS(행 단위 보안)를 끈다. 회사 사용 단계에서는 로그인과 RLS를 켠다.

create table if not exists documents (
  key text primary key,                 -- 'forecast', 'machines' 등 파이썬이 올리는 큰 JSON
  data jsonb not null,
  updated_at timestamptz default now()
);

create table if not exists inventory (
  item_type text primary key,           -- 품종 코드
  qty numeric not null default 0,       -- 현재고(개)
  updated_by text,
  updated_at timestamptz default now()
);

create table if not exists plan_versions (
  id bigserial primary key,
  week_start date not null,             -- 계획 주 시작(월요일)
  name text,
  published_at timestamptz,             -- 배포 시각(비어 있으면 작성 중)
  published_by text
);

create table if not exists plan_cells (
  id bigserial primary key,
  week_start date not null,
  machine text not null,                -- 부서코드|호기 (예: 1219|P3)
  day int not null,                     -- 0=월 ... 6=일
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
  reason text,                          -- 거래처 주문 변경 / 설비 고장 / 원부자재 부족 / 인원 부족 / 품질 / 기타
  memo text
);

alter table documents disable row level security;
alter table inventory disable row level security;
alter table plan_versions disable row level security;
alter table plan_cells disable row level security;
alter table plan_changes disable row level security;
