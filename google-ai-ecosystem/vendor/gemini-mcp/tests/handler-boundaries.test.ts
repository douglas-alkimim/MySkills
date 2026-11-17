import assert from "node:assert/strict";
import { test } from "node:test";
import { ToolHandlers, isMediaTimeoutMessage } from "../src/tools/handlers.js";

function fixture() {
  let conversation: { id: string; name: string; url: string } | null = {
    id: "synthetic-conversation",
    name: "Synthetic fixture",
    url: "https://gemini.google.com/app/synthetic",
  };
  let removals = 0;
  const sessionManager = {
    closeSessionsForConversation: async () => 1,
    getBrowserVisibility: () => ({ active: true, visible: false }),
    getStats: () => ({ active_sessions: 1, max_sessions: 5, session_timeout: 60, total_messages: 2 }),
  };
  const authManager = { getAuthStatus: async () => "valid" };
  const library = {
    getConversation: (id: string) => conversation?.id === id ? conversation : null,
    removeConversation: (id: string) => {
      if (conversation?.id !== id) return false;
      conversation = null;
      removals += 1;
      return true;
    },
  };
  const handlers = new ToolHandlers(sessionManager as never, authManager as never, library as never);
  return {
    handlers,
    get removals() { return removals; },
    restore() {
      conversation = { id: "synthetic-conversation", name: "Synthetic fixture", url: "https://gemini.google.com/app/synthetic" };
    },
    mutate() {
      if (conversation) conversation.name = "Changed after preview";
    },
  };
}

test("remove_conversation requires a state-bound single-use receipt", async () => {
  const item = fixture();
  const preview = await item.handlers.handleRemoveConversation({ id: "synthetic-conversation" });
  assert.equal(preview.success, true);
  assert.equal(preview.data?.status, "preview");
  assert.equal(preview.data?.removed, false);
  assert.equal(item.removals, 0);

  item.mutate();
  const changed = await item.handlers.handleRemoveConversation({
    id: "synthetic-conversation",
    receipt: preview.data?.receipt,
  });
  assert.equal(changed.success, false);
  assert.equal(item.removals, 0);

  const current = await item.handlers.handleRemoveConversation({ id: "synthetic-conversation" });
  const removed = await item.handlers.handleRemoveConversation({
    id: "synthetic-conversation",
    receipt: current.data?.receipt,
  });
  assert.equal(removed.success, true);
  assert.equal(removed.data?.status, "removed");
  assert.equal(item.removals, 1);

  item.restore();
  const reused = await item.handlers.handleRemoveConversation({
    id: "synthetic-conversation",
    receipt: current.data?.receipt,
  });
  assert.equal(reused.success, false);
  assert.equal(item.removals, 1);
});

test("health reports actual auth and active-browser visibility", async () => {
  const item = fixture();
  const health = await item.handlers.handleGetHealth();
  assert.equal(health.success, true);
  assert.equal(health.data?.authenticated, true);
  assert.equal(health.data?.auth_status, "valid");
  assert.equal(health.data?.browser_visible, false);
  assert.equal(health.data?.headless, true);
  assert.equal(health.data?.active_sessions, 1);
});

test("media timeout classification is explicit and does not depend on service text", () => {
  assert.equal(isMediaTimeoutMessage("MEDIA_TIMEOUT: generated video was not ready"), true);
  assert.equal(isMediaTimeoutMessage("MEDIA_CAPACITY: try later"), false);
});
