import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Demo6 RAG Streaming Chat",
  description: "Next.js UI for demo6 FastAPI SSE chat backend"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
