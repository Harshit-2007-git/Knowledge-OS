import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  experimental: {
    turbo: {
      root: "./",
    },
  },
};

export default nextConfig;