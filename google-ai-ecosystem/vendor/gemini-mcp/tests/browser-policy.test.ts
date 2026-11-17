import assert from "node:assert/strict";
import { mkdtemp, mkdir, rm, symlink } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import { parseLocale, parseTimezone } from "../src/config.js";
import { BrowserPolicy } from "../src/utils/browser-policy.js";

test("locale and timezone use validated explicit values", () => {
  assert.equal(parseLocale("pt-BR", "en"), "pt-BR");
  assert.equal(parseTimezone("America/Sao_Paulo", "UTC"), "America/Sao_Paulo");
  assert.throws(() => parseLocale("not a locale!", "en"), /Invalid/);
  assert.throws(() => parseTimezone("Mars/Olympus", "UTC"), /Invalid/);
});

test("browser launch policy contains no concealment flags", () => {
  const policy = new BrowserPolicy();
  const options = policy.launchOptions(
    {
      viewport: { width: 1024, height: 768 },
      locale: "pt-BR",
      timezoneId: "America/Sao_Paulo",
    } as never,
    true,
  );
  const rendered = JSON.stringify(options);
  assert.equal(rendered.includes("AutomationControlled"), false);
  assert.equal(options.headless, true);
  assert.equal(options.locale, "pt-BR");
  assert.equal(options.timezoneId, "America/Sao_Paulo");
});

test("managed profile boundary rejects sibling and external links", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "browser-policy-test-"));
  try {
    const managed = path.join(root, "instances");
    const valid = path.join(managed, "profile-1");
    const sibling = path.join(root, "instances-sibling");
    await Promise.all([
      mkdir(valid, { recursive: true }),
      mkdir(sibling, { recursive: true }),
    ]);
    const policy = new BrowserPolicy();
    await policy.assertExistingDescendant(managed, valid);
    await assert.rejects(policy.assertExistingDescendant(managed, sibling), /outside/);

    const link = path.join(managed, "external-link");
    try {
      await symlink(sibling, link, process.platform === "win32" ? "junction" : "dir");
      await assert.rejects(policy.assertExistingDescendant(managed, link), /outside/);
    } catch (error) {
      if (!(typeof error === "object" && error !== null && "code" in error && error.code === "EPERM")) throw error;
    }
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
