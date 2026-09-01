import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Note: `output: "standalone"` is used in the Docker deployment path.
  // On Vercel, we omit it so Vercel can use its own optimised output format.
};

export default nextConfig;
