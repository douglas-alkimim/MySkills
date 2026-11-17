import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

test("the unit-test command is finite and separate from server startup", async () => {
  const packageJson = JSON.parse(
    await readFile(new URL("../package.json", import.meta.url), "utf8"),
  ) as { scripts: Record<string, string> };

  assert.match(packageJson.scripts.test, /--test/);
  assert.doesNotMatch(packageJson.scripts.test, /src\/index\.ts|dist\/index\.js/);
  assert.equal(packageJson.scripts.smoke, "node scripts/server-lifecycle-smoke.mjs");
  assert.equal(packageJson.scripts["smoke:real"], "node scripts/mcp-smoke-test.mjs");
  assert.equal(packageJson.scripts.build, "tsc");
});

test("the baseline source and smoke harness remain present", async () => {
  const [entrypoint, smoke] = await Promise.all([
    readFile(new URL("../src/index.ts", import.meta.url), "utf8"),
    readFile(new URL("../scripts/server-lifecycle-smoke.mjs", import.meta.url), "utf8"),
  ]);

  assert.match(entrypoint, /class GeminiMCPServer/);
  assert.match(smoke, /timeout|setTimeout/i);
});
