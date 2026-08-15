import { copyFileSync, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const dist = join(root, "dist");
const sourceReport = join(root, "reports", "aria_pc_status.html");
const sourceReadiness = join(root, "reports", "external_readiness.json");
const sourceGutsHtml = join(root, "reports", "guts_gigaflops.html");
const sourceGutsInventory = join(root, "reports", "guts_gigaflops_source_inventory.json");
const sourceHosting = join(root, ".openai", "hosting.json");
const targetIndex = join(dist, "index.html");
const targetReportsDir = join(dist, "reports");
const targetGutsDir = join(dist, "guts-gigaflops");
const targetServerDir = join(dist, "server");
const targetOpenAiDir = join(dist, ".openai");
const targetReadiness = join(targetReportsDir, "external_readiness.json");
const targetGutsHtml = join(targetGutsDir, "index.html");
const targetGutsInventory = join(targetGutsDir, "guts_gigaflops_source_inventory.json");
const targetServer = join(targetServerDir, "index.js");

function serverSource(html, readiness) {
  return `const html = ${JSON.stringify(html)};\nconst readiness = ${JSON.stringify(JSON.parse(readiness), null, 2)};\n\nexport default {\n  async fetch(request) {\n    const url = new URL(request.url);\n    if (url.pathname === "/reports/external_readiness.json") {\n      return Response.json(readiness);\n    }\n    return new Response(html, {\n      headers: {\n        "content-type": "text/html; charset=utf-8",\n        "cache-control": "public, max-age=60"\n      }\n    });\n  }\n};\n`;
}

function build() {
  rmSync(dist, { recursive: true, force: true });
  mkdirSync(targetReportsDir, { recursive: true });
  mkdirSync(targetGutsDir, { recursive: true });
  mkdirSync(targetServerDir, { recursive: true });
  mkdirSync(targetOpenAiDir, { recursive: true });
  const html = readFileSync(sourceReport, "utf8");
  const readiness = readFileSync(sourceReadiness, "utf8");
  writeFileSync(targetIndex, html, "utf8");
  copyFileSync(sourceReport, join(targetReportsDir, "aria_pc_status.html"));
  copyFileSync(sourceReadiness, targetReadiness);
  if (existsSync(sourceGutsHtml)) {
    copyFileSync(sourceGutsHtml, targetGutsHtml);
  }
  if (existsSync(sourceGutsInventory)) {
    copyFileSync(sourceGutsInventory, targetGutsInventory);
  }
  const hosting = JSON.parse(readFileSync(sourceHosting, "utf8"));
  writeFileSync(join(targetOpenAiDir, "hosting.json"), JSON.stringify({ project_id: hosting.project_id }, null, 2) + "\n", "utf8");
  writeFileSync(targetServer, serverSource(html, readiness), "utf8");
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
  if (existsSync(sourceGutsHtml) && !existsSync(targetGutsHtml)) {
    throw new Error("dist/guts-gigaflops/index.html missing; run npm run build");
  }
  if (existsSync(sourceGutsInventory) && !existsSync(targetGutsInventory)) {
    throw new Error("dist/guts-gigaflops/guts_gigaflops_source_inventory.json missing; run npm run build");
  }
}

if (process.argv.includes("--check")) {
  check();
  console.log("site-build-ok");
} else {
  build();
  console.log("built dist");
}
