import assert from "node:assert/strict";
import { test } from "node:test";
import { Redactor } from "../src/utils/redaction.js";

test("redactor removes secrets and user content from nested values", () => {
  const redactor = new Redactor(Buffer.alloc(32, 1));
  const fixture = {
    prompt: "private user prompt",
    email: "person@example.com",
    password: "swordfish",
    headers: { authorization: "Bearer secret-token", cookie: "SID=secret" },
    url: "https://example.test/path?token=secret#private",
    nested: { query: "private query", status: "ok" },
  };
  const rendered = JSON.stringify(redactor.redact(fixture));

  for (const forbidden of ["private user prompt", "person@example.com", "swordfish", "secret-token", "SID=secret", "private query", "token=secret", "#private"]) {
    assert.equal(rendered.includes(forbidden), false, forbidden);
  }
  assert.match(rendered, /REDACTED/);
  assert.match(rendered, /status/);
});

test("logger-style labeled content and credentials are redacted", () => {
  const redactor = new Redactor(Buffer.alloc(32, 2));
  const value = redactor.redactText(
    'Question: "hello secret" Prompt: "draw secret" Query: "secret term" Authorization: Bearer abc.def Password=guessme',
  );
  assert.equal(value.includes("hello secret"), false);
  assert.equal(value.includes("draw secret"), false);
  assert.equal(value.includes("secret term"), false);
  assert.equal(value.includes("abc.def"), false);
  assert.equal(value.includes("guessme"), false);
});

test("correlation identifiers are stable within a process and do not expose input", () => {
  const redactor = new Redactor(Buffer.alloc(32, 3));
  const first = redactor.correlationId("session-user-value");
  assert.equal(first, redactor.correlationId("session-user-value"));
  assert.equal(first.includes("session-user-value"), false);
  assert.equal(first.length, 16);
});
