import { spawn } from "node:child_process";
import { mkdtemp, readdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const destination = await mkdtemp(path.join(tmpdir(), "gemini-mcp-package-"));
const packageRoot = fileURLToPath(new URL("..", import.meta.url));
const pnpmEntrypoint = process.env.npm_execpath;

if (!pnpmEntrypoint) {
  throw new Error("package:check must be run through pnpm so npm_execpath is available");
}

try {
  const distFiles = await walk(path.join(packageRoot, "dist"));
  const forbiddenArtifacts = distFiles.filter((file) => /stealth|fingerprint|human.?like/i.test(file));
  if (forbiddenArtifacts.length > 0) {
    throw new Error(`Forbidden stale build artifacts: ${forbiddenArtifacts.join(", ")}`);
  }

  const exitCode = await new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [pnpmEntrypoint, "pack", "--pack-destination", destination], {
      cwd: packageRoot,
      stdio: "inherit",
      windowsHide: true,
    });
    child.on("error", reject);
    child.on("exit", (code) => resolve(code ?? 1));
  });
  if (exitCode !== 0) throw new Error(`pnpm pack failed with exit code ${exitCode}`);
  const archives = (await readdir(destination)).filter((name) => name.endsWith(".tgz"));
  if (archives.length !== 1) throw new Error(`Expected one package archive, found ${archives.length}`);
  console.log(`PACKAGE_OK archive=${archives[0]}`);
} finally {
  await rm(destination, { recursive: true, force: true });
}

async function walk(root) {
  const result = [];
  for (const entry of await readdir(root, { withFileTypes: true })) {
    const absolute = path.join(root, entry.name);
    if (entry.isDirectory()) result.push(...await walk(absolute));
    else result.push(path.relative(root, absolute).replaceAll("\\", "/"));
  }
  return result;
}
