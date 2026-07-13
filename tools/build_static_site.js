import { copyFileSync, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const dist = join(root, "dist");
const sourceReport = join(root, "reports", "aria_pc_status.html");
const targetIndex = join(dist, "index.html");
const targetReportsDir = join(dist, "reports");
const targetReadiness = join(targetReportsDir, "external_readiness.json");
const sourceReadiness = join(root, "reports", "external_readiness.json");

function build() {
  rmSync(dist, { recursive: true, force: true });
  mkdirSync(targetReportsDir, { recursive: true });
  copyFileSync(sourceReport, targetIndex);
  copyFileSync(sourceReport, join(targetReportsDir, "aria_pc_status.html"));
  copyFileSync(sourceReadiness, targetReadiness);
}

function check() {
  if (!existsSync(targetIndex) || !existsSync(targetReadiness)) {
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
