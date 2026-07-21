import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AX 교육 사전진단",
  description: "AX 교육을 준비하기 위한 사전 인터뷰",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" className="h-full">
      <head>
        <link
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
