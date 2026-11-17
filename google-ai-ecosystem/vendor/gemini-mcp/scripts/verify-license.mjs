import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));
const packageMetadata = JSON.parse(await readFile(path.join(root, "package.json"), "utf8"));
const vendorMetadata = JSON.parse(await readFile(path.join(root, "VENDOR.json"), "utf8"));
const license = await readFile(path.join(root, "LICENSE"), "utf8");
const readme = await readFile(path.join(root, "README.md"), "utf8");

const failures = [];
if (packageMetadata.license !== "MIT") failures.push("package license must be MIT");
if (packageMetadata.private !== true) failures.push("vendored runtime package must remain private");
for (const required of ["README.md", "LICENSE", "VENDOR.json"]) {
  if (!packageMetadata.files?.includes(required)) failures.push(`package files must include ${required}`);
}
if (!license.includes("Copyright (c) 2025 Please Prompto!")) {
  failures.push("original copyright notice is missing");
}
if (!license.includes("The above copyright notice and this permission notice shall be included")) {
  failures.push("MIT notice-preservation condition is missing");
}
if (!vendorMetadata.source || !vendorMetadata.upstream_commit || !vendorMetadata.tree_sha256) {
  failures.push("VENDOR.json is missing required provenance fields");
}
if (!readme.includes("modified third-party MIT-licensed code")) {
  failures.push("README must disclose the component's derived MIT-licensed composition");
}

if (failures.length > 0) {
  throw new Error(`License verification failed:\n- ${failures.join("\n- ")}`);
}

console.log("LICENSE_OK license=MIT notice=preserved provenance=present package=private");
