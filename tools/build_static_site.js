import { copyFileSync, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const dist = join(root, "dist");
const sourceReport = join(root, "reports", "aria_pc_status.html");
const sourceReadiness = join(root, "reports", "external_readiness.json");
const sourceHosting = join(root, ".openai", "hosting.json");
const targetIndex = join(dist, "index.html");
const targetReportsDir = join(dist, "reports");
const targetServerDir = join(dist, "server");
const targetOpenAiDir = join(dist, ".openai");
const targetReadiness = join(targetReportsDir, "external_readiness.json");
const targetServer = join(targetServerDir, "index.js");

const serverSource = String.raw`import html from "../index.html";
import readiness from "../reports/external_readiness.json";

export default {
  async fetch(request) {
    const url = new URL(request.url);
    if (url.pathname === "/reports/external_readiness.json") {
      return Response.json(readiness);
    }
    return new Response(html, {
      headers: {
        "content-type": "text/html; charset=utf-8",
        "cache-control": "public, max-age=60"
      }
    });
  }
};
`;

function build() {
  rmSync(dist, { recursive: true, force: true });
  mkdirSync(targetReportsDir, { recursive: true });
  mkdirSync(targetServerDir, { recursive: true });
  mkdirSync(targetOpenAiDir, { recursive: true });
  copyFileSync(sourceReport, targetIndex);
  copyFileSync(sourceReport, join(targetReportsDir, "aria_pc_status.html"));
  copyFileSync(sourceReadiness, targetReadiness);
  const hosting = JSON.parse(readFileSync(sourceHosting, "utf8"));
  writeFileSync(join(targetOpenAiDir, "hosting.json"), JSON.stringify({ project_id: hosting.project_id }, null, 2) + "\n", "utf8");
  writeFileSync(targetServer, serverSource, "utf8");
}

function check() {
  if (!existsSync(targetIndex) || !existsSync(targetReadiness) || !existsSync(targetServer)) {
    throw new Error("dist is missing; run npm run build");
  }
  const index = readFileSync(targetIndex, "utf8");
  const source = readFileSync(sourceReport, "utf8");
  if (index !== source) {
    throw new Error("dist/index.html is stale; run npm run build");
  }
}

if (process.argv.includes("--check")) {
  check();
  console.log("site-build-ok");
} else {
  build();
  console.log("built dist");
}


