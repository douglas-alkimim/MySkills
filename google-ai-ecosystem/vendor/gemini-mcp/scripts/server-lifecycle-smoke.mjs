import { spawn } from "node:child_process";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const isolatedRoot = await mkdtemp(path.join(tmpdir(), "gemini-mcp-smoke-"));
const child = spawn(process.execPath, [path.join(repositoryRoot, "dist", "index.js")], {
  cwd: repositoryRoot,
  env: {
    ...process.env,
    APPDATA: path.join(isolatedRoot, "appdata"),
    LOCALAPPDATA: path.join(isolatedRoot, "localappdata"),
    XDG_CONFIG_HOME: path.join(isolatedRoot, "config"),
    XDG_DATA_HOME: path.join(isolatedRoot, "data"),
    HEADLESS: "true",
  },
  stdio: ["pipe", "pipe", "pipe"],
});

let stdout = "";
let stderr = "";
let completed = false;

const timeout = setTimeout(() => finish(3, "server lifecycle smoke timed out"), 15_000);

function send(message) {
  child.stdin.write(`${JSON.stringify(message)}\n`);
}

async function finish(code, message) {
  if (completed) return;
  completed = true;
  clearTimeout(timeout);
  child.stdin.end();
  const killTimer = setTimeout(() => child.kill(), 2_000);
  killTimer.unref();
  if (message) console.error(message);
  if (code !== 0 && stderr.trim()) console.error(stderr.slice(-4_000));
  await rm(isolatedRoot, { recursive: true, force: true });
  process.exitCode = code;
}

child.stderr.on("data", (chunk) => {
  stderr += chunk.toString();
});

child.stdout.on("data", (chunk) => {
  stdout += chunk.toString();
  const lines = stdout.split(/\r?\n/);
  stdout = lines.pop() ?? "";
  for (const line of lines) {
    if (!line.trim()) continue;
    let message;
    try {
      message = JSON.parse(line);
    } catch {
      continue;
    }
    if (message.id === 1 && message.result) {
      send({ jsonrpc: "2.0", method: "notifications/initialized" });
      send({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} });
    } else if (message.id === 2) {
      const tools = message.result?.tools;
      if (!Array.isArray(tools) || tools.length === 0) {
        void finish(2, "tools/list returned no tools");
      } else if (tools.some((tool) => tool.name === "cleanup_data")) {
        void finish(2, "restricted standard profile exposed cleanup_data");
      } else {
        send({
          jsonrpc: "2.0",
          id: 3,
          method: "tools/call",
          params: { name: "cleanup_data", arguments: {} },
        });
      }
    } else if (message.id === 3) {
      const responseText = message.result?.content?.find((item) => item.type === "text")?.text;
      const payload = responseText ? JSON.parse(responseText) : null;
      if (payload?.code !== "TOOL_NOT_AUTHORIZED" || message.result?.isError !== true) {
        void finish(2, "direct cleanup_data call was not denied before dispatch");
      } else {
        console.log("SMOKE_OK standard_tools=12 direct_call=denied");
        void finish(0);
      }
    }
  }
});

child.on("error", (error) => void finish(1, error.message));
child.on("exit", (code) => {
  if (!completed) void finish(code ?? 1, "server exited before tools/list completed");
});

send({
  jsonrpc: "2.0",
  id: 1,
  method: "initialize",
  params: {
    protocolVersion: "2024-11-05",
    capabilities: {},
    clientInfo: { name: "gemini-mcp-isolated-smoke", version: "1.0.0" },
  },
});
