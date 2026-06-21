import type { Metadata } from "next";
import { Instrument_Serif, Space_Grotesk } from "next/font/google";

import "./globals.css";

const headingFont = Instrument_Serif({
  subsets: ["latin"],
  variable: "--font-heading",
  weight: "400",
});

const bodyFont = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "Interviewing Agent",
  description: "Audio-first ML interview simulator with deep technical probing.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body
        className={`${headingFont.variable} ${bodyFont.variable}`}
        suppressHydrationWarning
      >
        {children}
      </body>
    </html>
  );
}
