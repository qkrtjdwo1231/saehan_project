/** @type {import('next').NextConfig} */
// 정적 내보내기: 모든 화면이 브라우저에서 그려지므로 서버 없이 web/out 폴더만 배포한다 (버셀 Root Directory 설정 불필요)
// env: 버셀에 SUPABASE_URL / SUPABASE_ANON_KEY 이름으로 넣어도 화면에서 쓸 수 있도록 빌드 때 NEXT_PUBLIC_ 이름으로 옮긴다
const nextConfig = {
  output: "export",
  trailingSlash: true,
  env: {
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL || "",
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.SUPABASE_ANON_KEY || "",
  },
};
export default nextConfig;
