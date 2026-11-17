import assert from "node:assert/strict";
import { mkdir, mkdtemp, readFile, realpath, rm, symlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import { CleanupManager, type CleanupRoots } from "../src/utils/cleanup-manager.js";
import { ConfirmationReceiptStore } from "../src/utils/confirmation-receipts.js";

async function fixture(): Promise<{ root: string; data: string; outside: string; roots: CleanupRoots }> {
  const root = await mkdtemp(path.join(tmpdir(), "gemini-cleanup-test-"));
  const data = path.join(root, "gemini-mcp-data");
  const outside = path.join(root, "unrelated-app-data");
  const roots: CleanupRoots = {
    dataDir: data,
    browserStateDir: path.join(data, "browser_state"),
    chromeProfileDir: path.join(data, "chrome_profile"),
    chromeInstancesDir: path.join(data, "chrome_profile_instances"),
    libraryPath: path.join(data, "library.json"),
  };
  await Promise.all([
    mkdir(roots.browserStateDir, { recursive: true }),
    mkdir(roots.chromeProfileDir, { recursive: true }),
    mkdir(roots.chromeInstancesDir, { recursive: true }),
    mkdir(outside, { recursive: true }),
  ]);
  await Promise.all([
    writeFile(path.join(roots.browserStateDir, "state.json"), "synthetic-state"),
    writeFile(path.join(roots.chromeProfileDir, "cookie.db"), "synthetic-cookie"),
    writeFile(roots.libraryPath, "synthetic-library"),
    writeFile(path.join(outside, "keep.txt"), "keep"),
  ]);
  return { root, data, outside, roots };
}

test("cleanup removes only the exact reviewed MCP-owned scope", async () => {
  const item = await fixture();
  try {
    const manager = new CleanupManager(item.roots);
    const preview = await manager.preview(true);
    const canonicalData = await realpath(item.data);
    assert.equal(preview.paths.every((entry) => {
      const relative = path.relative(canonicalData, entry);
      return relative !== ".." && !relative.startsWith(`..${path.sep}`) && !path.isAbsolute(relative);
    }), true);
    assert.equal(JSON.stringify(preview).includes("unrelated-app-data"), false);
    const result = await manager.execute(preview.receipt, true);
    assert.equal(result.success, true);
    assert.equal(await readFile(item.roots.libraryPath, "utf8"), "synthetic-library");
    assert.equal(await readFile(path.join(item.outside, "keep.txt"), "utf8"), "keep");

    const emptyPreview = await manager.preview(true);
    const emptyResult = await manager.execute(emptyPreview.receipt, true);
    assert.equal(emptyResult.success, true);
    assert.deepEqual(emptyResult.removedPaths, []);
  } finally {
    await rm(item.root, { recursive: true, force: true });
  }
});

test("scope change after preview is denied and receipt is single use", async () => {
  const item = await fixture();
  try {
    const manager = new CleanupManager(item.roots);
    const preview = await manager.preview(true);
    await writeFile(path.join(item.roots.browserStateDir, "changed.json"), "changed");
    await assert.rejects(manager.execute(preview.receipt, true), /changed|scope|state/i);
    await assert.rejects(manager.execute(preview.receipt, true), /unknown|used/i);
    assert.equal(await readFile(path.join(item.outside, "keep.txt"), "utf8"), "keep");
  } finally {
    await rm(item.root, { recursive: true, force: true });
  }
});

test("sibling roots and external directory links are rejected", async () => {
  const item = await fixture();
  try {
    const siblingRoots = { ...item.roots, browserStateDir: item.outside };
    await assert.rejects(new CleanupManager(siblingRoots).preview(true), /outside/);

    await rm(item.roots.chromeInstancesDir, { recursive: true, force: true });
    try {
      await symlink(item.outside, item.roots.chromeInstancesDir, process.platform === "win32" ? "junction" : "dir");
      await assert.rejects(new CleanupManager(item.roots).preview(true), /outside/);
    } catch (error) {
      if (!(typeof error === "object" && error !== null && "code" in error && error.code === "EPERM")) throw error;
    }
  } finally {
    await rm(item.root, { recursive: true, force: true });
  }
});

test("generic receipts bind operation, resource state, TTL and reuse", async () => {
  const store = new ConfirmationReceiptStore();
  const issued = store.issue("remove", ["resource-a"], "v1", 10_000);
  assert.throws(() => store.consume(issued.receipt, "remove", ["resource-a"], "v2"), /changed/);
  assert.throws(() => store.consume(issued.receipt, "remove", ["resource-a"], "v1"), /used|unknown/);

  const expired = store.issue("remove", ["resource-a"], "v1", -1);
  assert.throws(() => store.consume(expired.receipt, "remove", ["resource-a"], "v1"), /expired/);
});
