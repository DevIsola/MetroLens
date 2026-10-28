import type { NextConfig } from "next";

// The GitHub Pages project path is an opt-in *build-time* setting.
// This increment does not deploy or publish the generated files.
const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
if (basePath && !/^\/[A-Za-z0-9-]+(?:\/[A-Za-z0-9-]+)*$/.test(basePath)) {
  throw new Error("NEXT_PUBLIC_BASE_PATH must be empty or an absolute path without a trailing slash");
}

const config: NextConfig = {
  output: "export",
  trailingSlash: true,
  reactStrictMode: true,
  images: { unoptimized: true },
  ...(basePath ? { basePath } : {}),
};

export default config;
