import type { NextConfig } from "next";

const isDevelopment = process.env.NODE_ENV === "development";
const isStaticExport = process.env.NEXT_OUTPUT_EXPORT === "true";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  distDir: isDevelopment ? ".next-dev" : ".next",
  output: isStaticExport ? "export" : undefined,
};

export default nextConfig;
