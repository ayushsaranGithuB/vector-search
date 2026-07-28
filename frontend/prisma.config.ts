import { loadEnvConfig } from "@next/env";
import path from "path";

const frontendDir = process.cwd();
const backendDir = path.resolve(frontendDir, "..", "backend");

loadEnvConfig(backendDir);
loadEnvConfig(frontendDir);

import { defineConfig, env } from "@prisma/config";

export default defineConfig({
    schema: "./prisma/schema.prisma",
    datasource: {
        url: env("NEON_CONNECTION_STRING"),
    },
});
