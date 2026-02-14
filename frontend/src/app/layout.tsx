import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ProSim",
  description: "Workflow simulation — rapid napkin calculations",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-text antialiased">
        {children}
      </body>
    </html>
  );
}
