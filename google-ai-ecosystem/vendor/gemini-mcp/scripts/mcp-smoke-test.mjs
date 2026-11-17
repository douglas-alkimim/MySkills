import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const serverPath = path.join(repoRoot, "dist", "index.js");
const testName = process.argv[2] || "health";
const mediaTimeoutMs = process.argv[3] || "720000";
const headless = process.argv[4] || "true";

const tests = {
  health: { name: "get_health", arguments: {} },
  auth: { name: "setup_auth", arguments: { show_browser: true } },
  chat: {
    name: "ask_question",
    arguments: { question: "Quanto é 2 + 2? Responda somente com o algarismo." },
  },
  model: { name: "select_model", arguments: { model: "pro" } },
  model_fast: { name: "select_model", arguments: { model: "fast" } },
  model_thinking: { name: "select_model", arguments: { model: "thinking" } },
  image: {
    name: "use_gemini_tool",
    arguments: {
      tool: "create_image",
      prompt: "Gere uma ilustração digital simples e amigável de um boneco azul acenando, sobre fundo branco, sem texto.",
    },
  },
  video: {
    name: "use_gemini_tool",
    arguments: {
      tool: "create_video",
      prompt: [
        "Crie um vídeo curto, alegre e apropriado para todas as idades, de um boneco simpático",
        "olhando diretamente para a câmera, acenando com a mão e dizendo claramente em português: ‘Oi!’.",
        "Use expressão amigável, movimento natural, cenário colorido e duração aproximada de 5 a 8 segundos.",
      ].join(" "),
      ...(process.env.GEMINI_REFERENCE_IMAGE
        ? {
            attachments: [
              {
                path: process.env.GEMINI_REFERENCE_IMAGE,
                purpose: "character",
                description: "Use o mesmo boneco como personagem principal do vídeo.",
              },
            ],
          }
        : {}),
    },
  },
  research: {
    name: "use_gemini_tool",
    arguments: {
      tool: "deep_research",
      prompt: "Faça um teste curto de pesquisa aprofundada: explique em três tópicos o que é o Model Context Protocol.",
    },
  },
};

const test = tests[testName];
if (!test) {
  throw new Error(`Unknown test '${testName}'. Choose: ${Object.keys(tests).join(", ")}`);
}

const child = spawn(process.execPath, [serverPath], {
  cwd: repoRoot,
  env: {
    ...process.env,
    HEADLESS: headless,
    CONVERSATION_URL: "https://gemini.google.com/app",
    GEMINI_OUTPUT_DIR:
      process.env.GEMINI_OUTPUT_DIR || path.resolve(repoRoot, "..", "gemini-output"),
    MEDIA_GENERATION_TIMEOUT_MS: mediaTimeoutMs,
    RESEARCH_TIMEOUT_MS: process.env.RESEARCH_TIMEOUT_MS || "900000",
  },
  stdio: ["pipe", "pipe", "pipe"],
});

let stdoutBuffer = "";
let stderrBuffer = "";
let resultExitCode = 1;
let receivedResult = false;

child.stderr.on("data", (chunk) => {
  stderrBuffer += chunk.toString();
  if (stderrBuffer.length > 40_000) stderrBuffer = stderrBuffer.slice(-40_000);
});

const send = (message) => child.stdin.write(`${JSON.stringify(message)}\n`);
const shutdown = (exitCode) => {
  resultExitCode = exitCode;
  receivedResult = true;
  child.stdin.end();
  setTimeout(() => child.kill(), 15_000).unref();
};

child.stdout.on("data", (chunk) => {
  stdoutBuffer += chunk.toString();
  const lines = stdoutBuffer.split(/\r?\n/);
  stdoutBuffer = lines.pop() ?? "";

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
      send({ jsonrpc: "2.0", id: 2, method: "tools/call", params: test });
    } else if (message.method === "notifications/progress") {
      console.log("PROGRESS received");
    } else if (message.id === 2) {
      if (message.error) {
        console.log(`MCP_ERROR code=${String(message.error.code ?? "unknown")}`);
        shutdown(2);
        continue;
      }
      const responseText = message.result?.content?.find((item) => item.type === "text")?.text;
      let parsed;
      try {
        parsed = JSON.parse(responseText);
      } catch {
        parsed = null;
      }
      let passed = parsed?.success === true;
      if (passed && testName === "chat") {
        passed = /^4(?:\s|$)/.test(parsed?.data?.answer?.trimStart() || "");
      }
      if (passed && (testName === "image" || testName === "video")) {
        passed = Array.isArray(parsed?.data?.files) && parsed.data.files.length > 0;
      }
      const safeSummary = {
        test: testName,
        success: parsed?.success === true,
        code: typeof parsed?.code === "string" ? parsed.code : undefined,
        auth_status: typeof parsed?.data?.auth_status === "string"
          ? parsed.data.auth_status
          : typeof parsed?.auth_status === "string"
            ? parsed.auth_status
            : undefined,
        authenticated: typeof parsed?.data?.authenticated === "boolean" ? parsed.data.authenticated : undefined,
        browser_visible: typeof parsed?.data?.browser_visible === "boolean" ? parsed.data.browser_visible : undefined,
        headless: typeof parsed?.data?.headless === "boolean" ? parsed.data.headless : undefined,
        answer_matches_contract: testName === "chat" ? passed : undefined,
        result_characters: testName === "research" && typeof parsed?.data?.result === "string"
          ? parsed.data.result.length
          : undefined,
        files: Array.isArray(parsed?.data?.files) ? parsed.data.files : undefined,
        diagnostic_characters: stderrBuffer.length,
      };
      console.log(`MCP_SUMMARY ${JSON.stringify(safeSummary)}`);
      shutdown(passed ? 0 : 2);
    }
  }
});

child.on("error", (error) => {
  console.error(`CLIENT_ERROR ${error.message}`);
  process.exit(1);
});

child.on("exit", (code) => {
  if (!receivedResult && stderrBuffer.trim()) console.error(`SERVER_DIAGNOSTICS characters=${stderrBuffer.length}`);
  process.exit(receivedResult ? resultExitCode : (code ?? 1));
});

setTimeout(() => {
  console.error(`CLIENT_TIMEOUT ${testName}`);
  child.kill();
  process.exit(3);
}, 20 * 60_000).unref();

send({
  jsonrpc: "2.0",
  id: 1,
  method: "initialize",
  params: {
    protocolVersion: "2024-11-05",
    capabilities: {},
    clientInfo: { name: `gemini-mcp-${testName}-test`, version: "1.0.0" },
  },
});
