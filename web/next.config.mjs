/** @type {import('next').NextConfig} */
// 정적 내보내기: 모든 화면이 브라우저에서 그려지므로 서버 없이 web/out 폴더만 배포한다 (버셀 Root Directory 설정 불필요)
const nextConfig = {
  output: "export",
  trailingSlash: true,
};
export default nextConfig;
