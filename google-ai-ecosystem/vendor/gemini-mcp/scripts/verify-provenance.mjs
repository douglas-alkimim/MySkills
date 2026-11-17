import { createHash } from "node:crypto";
import { readFile, readdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));
const excludedDirectories = new Set(["dist", "node_modules", ".git", "coverage"]);
const excludedFiles = new Set(["VENDOR.json"]);
// The installer adds this receipt only to managed runtime copies. It is not
// vendored source and must not make an otherwise byte-identical release fail.
const runtimeMetadataFiles = new Set([".google-ai-ecosystem-runtime.json"]);

const packageMetadata = JSON.parse(await readFile(path.join(root, "package.json"), "utf8"));
const vendorMetadata = JSON.parse(await readFile(path.join(root, "VENDOR.json"), "utf8"));
const treeSha256 = await hashTree(root);

if (process.argv.includes("--compute")) {
  console.log(treeSha256);
  process.exit(0);
}

const failures = [];
if (vendorMetadata.local_version !== packageMetadata.version) {
  failures.push(`local_version ${vendorMetadata.local_version} does not match package ${packageMetadata.version}`);
}
if (!/^[0-9a-f]{40}$/.test(vendorMetadata.upstream_commit ?? "")) {
  failures.push("upstream_commit must be a full 40-character Git SHA");
}
if (vendorMetadata.tree_sha256 !== treeSha256) {
  failures.push(`tree_sha256 mismatch: expected ${vendorMetadata.tree_sha256}, computed ${treeSha256}`);
}
if (JSON.stringify(vendorMetadata.tree_hash_excludes) !== JSON.stringify(["VENDOR.json", "dist/", "node_modules/", ".git/", "coverage/"])) {
  failures.push("tree_hash_excludes does not match the verifier contract");
}

if (failures.length > 0) {
  throw new Error(`Provenance verification failed:\n- ${failures.join("\n- ")}`);
}

console.log(`PROVENANCE_OK version=${packageMetadata.version} tree_sha256=${treeSha256}`);

async function hashTree(directory) {
  const hash = createHash("sha256");
  for (const relativePath of await collectFiles(directory)) {
    hash.update(relativePath);
    hash.update("\0");
    hash.update(await readFile(path.join(directory, relativePath)));
    hash.update("\0");
  }
  return hash.digest("hex");
}

async function collectFiles(directory, prefix = "") {
  const files = [];
  const entries = await readdir(directory, { withFileTypes: true });
  entries.sort((left, right) => left.name.localeCompare(right.name, "en"));
  for (const entry of entries) {
    if (entry.isDirectory() && excludedDirectories.has(entry.name)) continue;
    const relativePath = prefix ? `${prefix}/${entry.name}` : entry.name;
    if (entry.isDirectory()) files.push(...await collectFiles(path.join(directory, entry.name), relativePath));
    else if (!excludedFiles.has(relativePath) && !runtimeMetadataFiles.has(relativePath)) files.push(relativePath);
  }
  return files;
}
