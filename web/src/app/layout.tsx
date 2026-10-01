import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Expense Diary",
  description: "A private view of your spending and transactions.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
