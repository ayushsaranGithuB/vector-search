import { defineConfig, env } from "@prisma/config";

export default defineConfig({
    schema: "./prisma/schema.prisma",
    datasource: {
        url: env("NEON_CONNECTION_STRING"),
    },
});
