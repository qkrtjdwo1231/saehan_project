// 모든 화면의 공통 틀(상단 메뉴, 담당자 선택)
import "./globals.css";
import Nav from "@/components/Nav";

export const metadata = { title: "새한프라텍 생산계획 보드", description: "출하예측 기반 주간 생산계획" };

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <body>
        <Nav />
        <main>{children}</main>
      </body>
    </html>
  );
}
