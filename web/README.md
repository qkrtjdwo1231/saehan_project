# 새한프라텍 생산계획 보드 (웹)

Next.js 화면 5개. 계산은 하지 않고 수파베이스(없으면 `public/data/*.json`)에서 읽어 보여주며, 재고·계획·변경 이력만 쓴다.

## 화면

| 경로 | 화면 | 데이터 |
|---|---|---|
| `/` | 홈. 다음 4주 총량 예측, 4주 소요량 상위 10 | documents.forecast |
| `/forecast` | 수요 예측. 품종×거래처, 유형, 1~4주 예측 | documents.forecast |
| `/plan` | 주간 생산계획. 설비×요일 격자, 배포, 배포 후 변경 사유 기록 | documents.machines, plan_cells, plan_versions, plan_changes |
| `/inventory` | 가용재고 보드. 현재고 입력, 소진 예상 | inventory, plan_cells |
| `/changes` | 변경 이력과 사유별 집계 | plan_changes |

## 처음 한 번 할 일

1. 수파베이스 SQL Editor에서 `../supabase/schema.sql` 실행 (표 5개).
2. 저장소 루트 `.env`에 `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `web/.env.local`에 `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` (둘 다 git 제외).
3. 예측 데이터 올리기 (저장소 루트에서)
   ```
   python -m pipeline.run "2025년 판매실적" data/processed
   python -m pipeline.forecast.produce data/processed data/web
   python pipeline/upload_supabase.py data/web
   ```
4. 버셀 프로젝트 설정
   - Root Directory: `web`
   - Environment Variables: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - 이후 `main`에 푸시하면 자동 배포

## 로컬 실행

```
cd web
npm install
npm run dev
```
수파베이스 환경변수가 없으면 `public/data/forecast.json`, `machines.json`을 읽고, 재고·계획·변경은 브라우저 저장소에만 남는다.

## 주의

시연용이라 수파베이스 표의 행 단위 보안(RLS)을 껐다. 주소와 anon key를 아는 사람은 누구나 읽고 쓸 수 있으므로, 회사에서 실제로 쓰기 전에는 로그인과 RLS를 켜야 한다.
