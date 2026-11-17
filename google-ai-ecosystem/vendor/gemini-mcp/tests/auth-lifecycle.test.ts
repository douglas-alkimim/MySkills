import assert from "node:assert/strict";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import { AuthManager } from "../src/auth/auth-manager.js";

async function authFixture() {
  const root = await mkdtemp(path.join(tmpdir(), "gemini-auth-test-"));
  const browserStateDir = path.join(root, "browser_state");
  const chromeProfileDir = path.join(root, "chrome_profile");
  await Promise.all([
    mkdir(browserStateDir, { recursive: true }),
    mkdir(chromeProfileDir, { recursive: true }),
  ]);
  const stateFilePath = path.join(browserStateDir, "state.json");
  const sessionFilePath = path.join(browserStateDir, "session.json");
  const manager = new AuthManager({ browserStateDir, chromeProfileDir, stateFilePath, sessionFilePath });
  return { root, browserStateDir, chromeProfileDir, stateFilePath, sessionFilePath, manager };
}

function state(expires: number) {
  return JSON.stringify({ cookies: [{ name: "SID", expires, value: "synthetic-cookie" }], origins: [] });
}

test("auth state machine distinguishes unconfigured, valid, expired and repairable", async () => {
  const item = await authFixture();
  try {
    assert.equal(await item.manager.getAuthStatus(), "unconfigured");
    await writeFile(item.stateFilePath, state(Date.now() / 1000 + 3600));
    assert.equal(await item.manager.getAuthStatus(), "valid");
    await writeFile(item.stateFilePath, state(Date.now() / 1000 - 1));
    assert.equal(await item.manager.getAuthStatus(), "expired");
    await writeFile(item.stateFilePath, "{broken");
    assert.equal(await item.manager.getAuthStatus(), "repairable");
  } finally {
    await rm(item.root, { recursive: true, force: true });
  }
});

test("valid setup is a no-op and preserves the existing profile", async () => {
  const item = await authFixture();
  try {
    await writeFile(item.stateFilePath, state(Date.now() / 1000 + 3600));
    const marker = path.join(item.chromeProfileDir, "marker.txt");
    await writeFile(marker, "preserve-me");
    assert.equal(await item.manager.performSetup(), true);
    assert.equal(await readFile(marker, "utf8"), "preserve-me");
    assert.equal(await item.manager.getAuthStatus(), "valid");
  } finally {
    await rm(item.root, { recursive: true, force: true });
  }
});

test("browser state and session state use hardened atomic storage", async () => {
  const item = await authFixture();
  try {
    const context = {
      storageState: async () => JSON.parse(state(Date.now() / 1000 + 3600)),
    };
    const page = { evaluate: async () => JSON.stringify({ synthetic: "session" }) };
    assert.equal(await item.manager.saveBrowserState(context as never, page as never), true);
    assert.equal(JSON.parse(await readFile(item.stateFilePath, "utf8")).cookies[0].name, "SID");
    assert.deepEqual(JSON.parse(await readFile(item.sessionFilePath, "utf8")), { synthetic: "session" });
  } finally {
    await rm(item.root, { recursive: true, force: true });
  }
});

test("account-switch preview binds the current auth version and is non-destructive", async () => {
  const item = await authFixture();
  try {
    await writeFile(item.stateFilePath, state(Date.now() / 1000 + 3600));
    const preview = await item.manager.previewAccountSwitch();
    assert.equal(await item.manager.getAuthStatus(), "switch_requested");
    assert.equal((await readFile(item.stateFilePath, "utf8")).includes("synthetic-cookie"), true);
    await writeFile(item.sessionFilePath, "changed-after-preview");
    await assert.rejects(item.manager.consumeAccountSwitchReceipt(preview.receipt), /changed/);
    assert.equal((await readFile(item.stateFilePath, "utf8")).includes("synthetic-cookie"), true);
  } finally {
    await rm(item.root, { recursive: true, force: true });
  }
});

test("failed confirmed account switch restores the complete recoverable snapshot", async () => {
  const item = await authFixture();
  try {
    const originalState = state(Date.now() / 1000 + 3600);
    await writeFile(item.stateFilePath, originalState);
    await writeFile(item.sessionFilePath, JSON.stringify({ marker: "original-session" }));
    const marker = path.join(item.chromeProfileDir, "profile-marker.txt");
    await writeFile(marker, "original-profile");
    const preview = await item.manager.previewAccountSwitch();

    (item.manager as unknown as { performSetup: () => Promise<boolean> }).performSetup = async () => false;
    assert.equal(await item.manager.performAccountSwitch(preview.receipt), false);
    assert.equal(await readFile(item.stateFilePath, "utf8"), originalState);
    assert.deepEqual(JSON.parse(await readFile(item.sessionFilePath, "utf8")), { marker: "original-session" });
    assert.equal(await readFile(marker, "utf8"), "original-profile");
    assert.equal(await item.manager.getAuthStatus(), "failed_recoverable");
  } finally {
    await rm(item.root, { recursive: true, force: true });
  }
});

test("confirmed account switch removes only reviewed state and accepts the replacement", async () => {
  const item = await authFixture();
  try {
    await writeFile(item.stateFilePath, state(Date.now() / 1000 + 3600));
    await writeFile(item.sessionFilePath, JSON.stringify({ marker: "old" }));
    const unrelated = path.join(item.browserStateDir, "unrelated.json");
    await writeFile(unrelated, JSON.stringify({ preserve: true }));
    const preview = await item.manager.previewAccountSwitch();

    (item.manager as unknown as { performSetup: () => Promise<boolean> }).performSetup = async () => {
      await writeFile(item.stateFilePath, state(Date.now() / 1000 + 7200));
      await writeFile(item.sessionFilePath, JSON.stringify({ marker: "new" }));
      return true;
    };
    assert.equal(await item.manager.performAccountSwitch(preview.receipt), true);
    assert.deepEqual(JSON.parse(await readFile(item.sessionFilePath, "utf8")), { marker: "new" });
    assert.deepEqual(JSON.parse(await readFile(unrelated, "utf8")), { preserve: true });
    assert.equal(await item.manager.getAuthStatus(), "valid");
  } finally {
    await rm(item.root, { recursive: true, force: true });
  }
});
