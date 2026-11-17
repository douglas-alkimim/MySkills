import assert from "node:assert/strict";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import { SettingsManager } from "../src/utils/settings-manager.js";
import { CliHandler } from "../src/utils/cli-handler.js";
import { ToolAuthorizationPolicy } from "../src/utils/tool-authorization.js";

async function withSettingsFile(run: (file: string) => Promise<void>): Promise<void> {
  const root = await mkdtemp(path.join(tmpdir(), "gemini-settings-test-"));
  try {
    await run(path.join(root, "settings.json"));
  } finally {
    await rm(root, { recursive: true, force: true });
  }
}

test("missing and invalid settings fail closed to explicit standard", async () => {
  await withSettingsFile(async (file) => {
    const missing = new SettingsManager(file);
    assert.equal(missing.getEffectiveSettings({}).profile, "standard");
    assert.equal(missing.isToolAllowed("cleanup_data", {}), false);

    await writeFile(file, "{invalid json", "utf8");
    const invalidJson = new SettingsManager(file);
    assert.equal(invalidJson.getEffectiveSettings({}).profile, "standard");
    assert.equal(invalidJson.getDiagnostics()[0]?.code, "SETTINGS_INVALID");

    await writeFile(file, JSON.stringify({ profile: "owner", disabledTools: [] }), "utf8");
    const invalidProfile = new SettingsManager(file);
    assert.equal(invalidProfile.getEffectiveSettings({}).profile, "standard");
    assert.equal(invalidProfile.isToolAllowed("re_auth", {}), false);
  });
});

test("restricted profile persists across a new manager process boundary", async () => {
  await withSettingsFile(async (file) => {
    const first = new SettingsManager(file);
    await first.saveSettings({ profile: "minimal", disabledTools: ["ask_question"] });
    const restarted = new SettingsManager(file);
    assert.equal(restarted.getEffectiveSettings({}).profile, "minimal");
    assert.equal(restarted.isToolAllowed("ask_question", {}), false);
    assert.equal(restarted.isToolAllowed("get_health", {}), true);
  });
});

test("full requires a valid explicit setting and invalid env cannot elevate", async () => {
  await withSettingsFile(async (file) => {
    const settings = new SettingsManager(file);
    assert.equal(settings.isToolAllowed("cleanup_data", {}), false);
    await settings.saveSettings({ profile: "full", disabledTools: [] });
    const explicit = new SettingsManager(file);
    assert.equal(explicit.isToolAllowed("cleanup_data", {}), true);
    assert.equal(explicit.getEffectiveSettings({ CONVERSATIONLM_PROFILE: "invalid" }).profile, "standard");
    assert.equal(explicit.isToolAllowed("cleanup_data", { CONVERSATIONLM_PROFILE: "invalid" }), false);
  });
});

test("discovery and direct call use the same authorization decision before side effects", async () => {
  await withSettingsFile(async (file) => {
    const settings = new SettingsManager(file);
    const tools = [{ name: "get_health" }, { name: "cleanup_data" }] as never;
    assert.deepEqual(settings.filterTools(tools, {}).map((tool) => tool.name), ["get_health"]);

    let sideEffects = 0;
    const policy = new ToolAuthorizationPolicy(settings);
    const denied = policy.authorize("cleanup_data");
    if (denied === null) sideEffects += 1;
    assert.equal(denied?.code, "TOOL_NOT_AUTHORIZED");
    assert.equal(sideEffects, 0);
  });
});

test("config reset returns to the restricted standard profile", async () => {
  await withSettingsFile(async (file) => {
    const manager = new SettingsManager(file);
    await manager.saveSettings({ profile: "full", disabledTools: [] });
    const cli = new CliHandler(manager);
    await cli.handleCommand(["config", "reset"]);
    assert.equal(manager.getEffectiveSettings({}).profile, "standard");
    assert.equal(manager.isToolAllowed("cleanup_data", {}), false);
  });
});
