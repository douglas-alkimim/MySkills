import assert from "node:assert/strict";
import { mkdtemp, readFile, readdir, rm, stat } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import { SecureStorage } from "../src/utils/secure-storage.js";

test("secure storage atomically replaces content and leaves no temporary file", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "secure-storage-test-"));
  try {
    const target = path.join(root, "state.json");
    const storage = new SecureStorage();
    await storage.atomicWrite(target, '{"version":1}');
    await storage.atomicWrite(target, '{"version":2}');
    assert.equal(await readFile(target, "utf8"), '{"version":2}');
    assert.deepEqual((await readdir(root)).sort(), ["state.json"]);
    await storage.verify(target);
    if (process.platform !== "win32") {
      assert.equal((await stat(target)).mode & 0o077, 0);
    }
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
