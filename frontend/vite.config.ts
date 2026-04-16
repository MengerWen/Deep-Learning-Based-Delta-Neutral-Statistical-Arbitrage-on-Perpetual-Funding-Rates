import { defineConfig } from "vite";

const repositoryName = process.env.GITHUB_REPOSITORY?.split("/")[1];
const defaultBase =
  process.env.SHOWCASE_BASE_PATH ??
  (process.env.GITHUB_ACTIONS && repositoryName ? `/${repositoryName}/` : "/");

export default defineConfig({
  base: defaultBase,
  server: {
    port: 5173,
  },
});
