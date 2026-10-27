// 수파베이스 클라이언트. 환경변수가 없으면 null을 돌려주고, 데이터 계층이 로컬 JSON과 브라우저 저장소로 대신한다
import { createClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

export const supabase = url && key ? createClient(url, key) : null;
