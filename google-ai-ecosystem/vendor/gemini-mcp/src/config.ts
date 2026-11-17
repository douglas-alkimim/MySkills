/**
 * Configuration for Gemini App MCP Server
 *
 * Config Priority (highest to lowest):
 * 1. Hardcoded Defaults (works out of the box!)
 * 2. Environment Variables (optional, for advanced users)
 * 3. Tool Parameters (passed by the MCP client at runtime)
 *
 * No config.json file needed - all settings via ENV or tool parameters!
 */

import envPaths from "env-paths";
import fs from "fs";
import path from "path";

// Cross-platform data paths (unified without -nodejs suffix)
// Linux: ~/.local/share/gemini-mcp/
// macOS: ~/Library/Application Support/gemini-mcp/
// Windows: %APPDATA%\gemini-mcp\
// IMPORTANT: Pass empty string suffix to disable envPaths' default '-nodejs' suffix!
const paths = envPaths("gemini-mcp", {suffix: ""});

/**
 * Google Gemini Auth URL (used by setup_auth)
 * This is the base Google login URL that redirects to Gemini App
 */
export const GEMINI_AUTH_URL =
  "https://accounts.google.com/v3/signin/identifier?continue=https%3A%2F%2Fgemini.google.com%2Fapp&flowName=GlifWebSignIn&flowEntry=ServiceLogin";

export interface Config {
  // Gemini App - optional, used for legacy default conversation
  geminiUrl: string;

  // Browser Settings
  headless: boolean;
  browserTimeout: number;
  viewport: { width: number; height: number };
  locale: string;
  timezoneId: string;

  // Session Management
  maxSessions: number;
  sessionTimeout: number; // in seconds

  // Paths
  configDir: string;
  dataDir: string;
  browserStateDir: string;
  chromeProfileDir: string;
  chromeInstancesDir: string;
  outputDir: string;

  // Long-running Gemini tools
  mediaGenerationTimeoutMs: number;
  researchTimeoutMs: number;

  // Library Configuration (optional, for default conversation metadata)
  conversationDescription: string;
  conversationTopics: string[];
  conversationContentTypes: string[];
  conversationUseCases: string[];

  // Multi-instance profile strategy
  profileStrategy: "auto" | "single" | "isolated";
  cloneProfileOnIsolated: boolean;
  cleanupInstancesOnStartup: boolean;
  cleanupInstancesOnShutdown: boolean;
  instanceProfileTtlHours: number;
  instanceProfileMaxCount: number;
}

/**
 * Default Configuration (works out of the box!)
 */
const DEFAULTS: Config = {
  // Gemini App
  geminiUrl: "https://gemini.google.com/app",

  // Browser Settings
  headless: true,
  browserTimeout: 30000,
  viewport: { width: 1024, height: 768 },
  locale: resolvedLocale(),
  timezoneId: resolvedTimezone(),

  // Session Management
  maxSessions: 10,
  sessionTimeout: 900, // 15 minutes

  // Paths (cross-platform via env-paths)
  configDir: paths.config,
  dataDir: paths.data,
  browserStateDir: path.join(paths.data, "browser_state"),
  chromeProfileDir: path.join(paths.data, "chrome_profile"),
  chromeInstancesDir: path.join(paths.data, "chrome_profile_instances"),
  outputDir: path.join(paths.data, "generated"),

  // Long-running Gemini tools
  mediaGenerationTimeoutMs: 12 * 60 * 1000,
  researchTimeoutMs: 15 * 60 * 1000,

  // Library Configuration
  conversationDescription: "General knowledge base",
  conversationTopics: ["General topics"],
  conversationContentTypes: ["documentation", "examples"],
  conversationUseCases: ["General research"],

  // Multi-instance strategy
  profileStrategy: "auto",
  cloneProfileOnIsolated: false,
  cleanupInstancesOnStartup: true,
  cleanupInstancesOnShutdown: true,
  instanceProfileTtlHours: 72,
  instanceProfileMaxCount: 20,
};


/**
 * Parse boolean from string (for env vars)
 */
function parseBoolean(value: string | undefined, defaultValue: boolean): boolean {
  if (value === undefined) return defaultValue;
  const lower = value.toLowerCase();
  if (lower === "true" || lower === "1") return true;
  if (lower === "false" || lower === "0") return false;
  return defaultValue;
}

/**
 * Parse integer from string (for env vars)
 */
function parseInteger(value: string | undefined, defaultValue: number): number {
  if (value === undefined) return defaultValue;
  const parsed = Number.parseInt(value, 10);
  return Number.isNaN(parsed) ? defaultValue : parsed;
}

/**
 * Parse comma-separated array (for env vars)
 */
function parseArray(value: string | undefined, defaultValue: string[]): string[] {
  if (!value) return defaultValue;
  return value.split(",").map((s) => s.trim()).filter((s) => s.length > 0);
}

function resolvedLocale(): string {
  return Intl.DateTimeFormat().resolvedOptions().locale || "en";
}

function resolvedTimezone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
}

export function detectLegacyCredentialAuth(
  environment: NodeJS.ProcessEnv = process.env
): Error | null {
  const enabledKey = ["AUTO", "LOGIN", "ENABLED"].join("_");
  const emailKey = ["LOGIN", "EMAIL"].join("_");
  const passwordKey = ["LOGIN", "PASSWORD"].join("_");
  const owns = (key: string): boolean => Object.prototype.hasOwnProperty.call(environment, key);
  const credentialKeyPresent = owns(emailKey) || owns(passwordKey);
  const enabledValue = owns(enabledKey) ? environment[enabledKey]?.trim().toLowerCase() : undefined;
  if (!credentialKeyPresent && enabledValue !== "true" && enabledValue !== "1") {
    return null;
  }
  const error = new Error(
    "LEGACY_AUTO_LOGIN_UNSUPPORTED: remove legacy credential-auth environment keys, restart the MCP, then call setup_auth(show_browser=true)."
  );
  error.name = "LegacyAutoLoginUnsupportedError";
  return error;
}

export function parseLocale(value: string | undefined, defaultValue: string): string {
  if (value === undefined) return defaultValue;
  try {
    return new Intl.Locale(value).toString();
  } catch {
    throw new Error("Invalid GEMINI_BROWSER_LOCALE value");
  }
}

export function parseTimezone(value: string | undefined, defaultValue: string): string {
  if (value === undefined) return defaultValue;
  try {
    new Intl.DateTimeFormat("en", { timeZone: value }).format();
    return value;
  } catch {
    throw new Error("Invalid GEMINI_BROWSER_TIMEZONE value");
  }
}

/**
 * Apply environment variable overrides (legacy support)
 */
function applyEnvOverrides(config: Config): Config {
  return {
    ...config,
    // Override with env vars if present
    geminiUrl: process.env.CONVERSATION_URL || config.geminiUrl,
    headless: parseBoolean(process.env.HEADLESS, config.headless),
    browserTimeout: parseInteger(process.env.BROWSER_TIMEOUT, config.browserTimeout),
    locale: parseLocale(process.env.GEMINI_BROWSER_LOCALE, config.locale),
    timezoneId: parseTimezone(process.env.GEMINI_BROWSER_TIMEZONE, config.timezoneId),
    maxSessions: parseInteger(process.env.MAX_SESSIONS, config.maxSessions),
    sessionTimeout: parseInteger(process.env.SESSION_TIMEOUT, config.sessionTimeout),
    outputDir: process.env.GEMINI_OUTPUT_DIR || config.outputDir,
    mediaGenerationTimeoutMs: parseInteger(
      process.env.MEDIA_GENERATION_TIMEOUT_MS,
      config.mediaGenerationTimeoutMs
    ),
    researchTimeoutMs: parseInteger(
      process.env.RESEARCH_TIMEOUT_MS,
      config.researchTimeoutMs
    ),
    conversationDescription: process.env.CONVERSATION_DESCRIPTION || config.conversationDescription,
    conversationTopics: parseArray(process.env.CONVERSATION_TOPICS, config.conversationTopics),
    conversationContentTypes: parseArray(process.env.CONVERSATION_CONTENT_TYPES, config.conversationContentTypes),
    conversationUseCases: parseArray(process.env.CONVERSATION_USE_CASES, config.conversationUseCases),
    profileStrategy: (process.env.CONVERSATION_PROFILE_STRATEGY as any) || config.profileStrategy,
    cloneProfileOnIsolated: parseBoolean(process.env.CONVERSATION_CLONE_PROFILE, config.cloneProfileOnIsolated),
    cleanupInstancesOnStartup: parseBoolean(process.env.CONVERSATION_CLEANUP_ON_STARTUP, config.cleanupInstancesOnStartup),
    cleanupInstancesOnShutdown: parseBoolean(process.env.CONVERSATION_CLEANUP_ON_SHUTDOWN, config.cleanupInstancesOnShutdown),
    instanceProfileTtlHours: parseInteger(process.env.CONVERSATION_INSTANCE_TTL_HOURS, config.instanceProfileTtlHours),
    instanceProfileMaxCount: parseInteger(process.env.CONVERSATION_INSTANCE_MAX_COUNT, config.instanceProfileMaxCount),
  };
}

/**
 * Build final configuration
 * Priority: Defaults → Environment Variables → Tool Parameters (at runtime)
 * No config.json files - everything via ENV or tool parameters!
 */
function buildConfig(): Config {
  const legacyCredentialAuth = detectLegacyCredentialAuth();
  if (legacyCredentialAuth) throw legacyCredentialAuth;
  return applyEnvOverrides(DEFAULTS);
}

/**
 * Global configuration instance
 */
export const CONFIG: Config = buildConfig();

/**
 * Ensure all required directories exist
 * NOTE: We do NOT create configDir - it's not needed!
 */
export function ensureDirectories(): void {
  const dirs = [
    CONFIG.dataDir,
    CONFIG.browserStateDir,
    CONFIG.chromeProfileDir,
    CONFIG.chromeInstancesDir,
    CONFIG.outputDir,
  ];

  for (const dir of dirs) {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  }
}


/**
 * Browser options that can be passed via tool parameters
 */
export interface BrowserOptions {
  show?: boolean;
  headless?: boolean;
  timeout_ms?: number;
  locale?: string;
  timezone_id?: string;
  viewport?: {
    width?: number;
    height?: number;
  };
}

/**
 * Apply browser options to CONFIG (returns modified copy, doesn't mutate global CONFIG)
 */
export function applyBrowserOptions(
  options?: BrowserOptions,
  legacyShowBrowser?: boolean
): Config {
  const config = { ...CONFIG };

  // Handle legacy show_browser parameter
  if (legacyShowBrowser !== undefined) {
    config.headless = !legacyShowBrowser;
  }

  // Apply browser_options (takes precedence over legacy parameter)
  if (options) {
    if (options.show !== undefined) {
      config.headless = !options.show;
    }
    if (options.headless !== undefined) {
      config.headless = options.headless;
    }
    if (options.timeout_ms !== undefined) {
      config.browserTimeout = options.timeout_ms;
    }
    config.locale = parseLocale(options.locale, config.locale);
    config.timezoneId = parseTimezone(options.timezone_id, config.timezoneId);
    if (options.viewport) {
      config.viewport = {
        width: options.viewport.width ?? config.viewport.width,
        height: options.viewport.height ?? config.viewport.height,
      };
    }
  }

  return config;
}

// Create directories on import
ensureDirectories();
