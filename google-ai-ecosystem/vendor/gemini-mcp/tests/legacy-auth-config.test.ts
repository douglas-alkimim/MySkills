import assert from "node:assert/strict";
import { test } from "node:test";
import { detectLegacyCredentialAuth } from "../src/config.js";

test("legacy credential fields fail safely without exposing their values", () => {
  const marker = "do-not-log-this-value";
  for (const fixture of [
    { LOGIN_EMAIL: marker },
    { LOGIN_PASSWORD: marker },
    { AUTO_LOGIN_ENABLED: "true" },
  ]) {
    const error = detectLegacyCredentialAuth(fixture);
    assert.ok(error);
    assert.match(error.message, /LEGACY_AUTO_LOGIN_UNSUPPORTED/);
    assert.doesNotMatch(error.message, new RegExp(marker));
    assert.match(error.message, /setup_auth/);
  }
});

test("an old disabled flag is inert during registration migration", () => {
  assert.equal(detectLegacyCredentialAuth({ AUTO_LOGIN_ENABLED: "false" }), null);
  assert.equal(detectLegacyCredentialAuth({}), null);
});
