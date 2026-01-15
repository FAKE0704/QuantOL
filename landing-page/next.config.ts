import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 移除 standalone 输出模式，改用标准的 next start
  // standalone 模式用于 Docker/容器化部署
  eslint: {
    // 在生产构建时忽略 ESLint 错误
    ignoreDuringBuilds: true,
  },
  typescript: {
    // 在生产构建时忽略 TypeScript 错误
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
