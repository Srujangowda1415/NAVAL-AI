import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone output produces a minimal self-contained server bundle —
  // used by the multi-stage Dockerfile so the production image doesn't
  // need to carry the full node_modules tree.
  output: "standalone",
};

export default nextConfig;
