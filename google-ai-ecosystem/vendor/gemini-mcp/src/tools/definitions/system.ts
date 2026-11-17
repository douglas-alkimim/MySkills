import { Tool } from "@modelcontextprotocol/sdk/types.js";

export const systemTools: Tool[] = [
  {
    name: "get_health",
    description:
      "Get server health status including authentication state, active sessions, and configuration. " +
      "Use this to verify readiness and the actual browser visibility. Authentication recovery never implies cleanup.",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },
  {
    name: "setup_auth",
    description:
      "Google authentication for Gemini App access - opens a browser window for manual login to your Google account. " +
      "Waits for the bounded interactive login flow to complete. " +
      "Use 'get_health' tool afterwards to verify authentication was saved successfully. " +
      "Use this for initial authentication. If valid state already exists it is preserved and verified. " +
      "For non-destructive recovery use re_auth(mode='repair'). Account switching is a separate confirmed operation.",
    inputSchema: {
      type: "object",
      properties: {
        show_browser: {
          type: "boolean",
          description:
            "Show browser window (simple version). Default: true for setup. " +
            "For advanced control, use browser_options instead.",
        },
        browser_options: {
          type: "object",
          description:
            "Optional deterministic browser settings for visibility and timeout.",
          properties: {
            show: {
              type: "boolean",
              description: "Show browser window (default: true for setup)",
            },
            headless: {
              type: "boolean",
              description: "Run browser in headless mode (default: false for setup)",
            },
            timeout_ms: {
              type: "number",
              description: "Browser operation timeout in milliseconds (default: 30000)",
            },
          },
        },
      },
    },
  },
  {
    name: "re_auth",
    description:
      "Recover authentication or explicitly switch accounts. mode='repair' preserves a recoverable snapshot and rolls back on failure. " +
      "mode='switch_account' first returns an operation-bound preview receipt; only a second call with the confirmed receipt may clear the old MCP profile. " +
      "Quota/capacity messages never trigger an account switch automatically.",
    inputSchema: {
      type: "object",
      properties: {
        mode: {
          type: "string",
          enum: ["repair", "switch_account"],
          description: "repair is non-destructive and is the default; switch_account requires a preview receipt.",
        },
        receipt: {
          type: "string",
          description: "Opaque receipt from the switch_account preview. Omit on the first switch_account call.",
        },
        show_browser: {
          type: "boolean",
          description:
            "Show browser window (simple version). Default: true for re-auth. " +
            "For advanced control, use browser_options instead.",
        },
        browser_options: {
          type: "object",
          description:
            "Optional deterministic browser settings for visibility and timeout.",
          properties: {
            show: {
              type: "boolean",
              description: "Show browser window (default: true for re-auth)",
            },
            headless: {
              type: "boolean",
              description: "Run browser in headless mode (default: false for re-auth)",
            },
            timeout_ms: {
              type: "number",
              description: "Browser operation timeout in milliseconds (default: 30000)",
            },
          },
        },
      },
    },
  },
  {
    name: "cleanup_data",
    description:
      "Preview or remove Gemini MCP-owned authentication state and browser profiles only. " +
      "The first call omits receipt and returns exact canonical paths plus a short-lived single-use receipt. " +
      "After the user reviews that preview and explicitly confirms it, call again with the same receipt and preserve_library value. " +
      "Any path, state, TTL or scope change is denied. This tool never scans or removes npm, other applications, editor data, general caches or trash.",
    inputSchema: {
      type: "object",
      properties: {
        receipt: {
          type: "string",
          description: "Opaque receipt returned by the exact preview the user confirmed. Omit to preview.",
        },
        preserve_library: {
          type: "boolean",
          description:
            "Preserve the MCP conversation library. Defaults to true and must match preview and execution.",
          default: true,
        },
      },
    },
  },
];
