import { loadEnvConfig } from "@next/env";
import path from "path";

const backendDir = path.resolve(process.cwd(), "..", "backend");
loadEnvConfig(backendDir);

export const databaseUrl = process.env.NEON_CONNECTION_STRING;
