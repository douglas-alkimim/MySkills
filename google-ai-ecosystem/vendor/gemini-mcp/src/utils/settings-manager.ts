import { existsSync, mkdirSync, readFileSync } from "node:fs";
import path from "node:path";
import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import { CONFIG } from "../config.js";
import { log } from "./logger.js";
import { secureStorage } from "./secure-storage.js";

export type ProfileName = "minimal" | "standard" | "full";

export interface Settings {
  profile: ProfileName;
  disabledTools: string[];
  customSettings?: Record<string, unknown>;
}

export interface SettingsDiagnostic {
  code: "SETTINGS_MISSING" | "SETTINGS_INVALID" | "SETTINGS_UNREADABLE" | "ENV_PROFILE_INVALID";
  message: string;
}

export const KNOWN_TOOL_NAMES = [
  "ask_question",
  "select_model",
  "use_gemini_tool",
  "add_conversation",
  "list_conversations",
  "get_conversation",
  "select_conversation",
  "update_conversation",
  "remove_conversation",
  "search_conversations",
  "get_library_stats",
  "list_sessions",
  "close_session",
  "reset_session",
  "get_health",
  "setup_auth",
  "re_auth",
  "cleanup_data",
] as const;

const KNOWN_TOOLS = new Set<string>(KNOWN_TOOL_NAMES);
const DEFAULT_SETTINGS: Settings = { profile: "standard", disabledTools: [] };

const PROFILES: Readonly<Record<ProfileName, readonly string[]>> = {
  minimal: ["ask_question", "get_health", "list_conversations", "select_conversation", "get_conversation"],
  standard: [
    "ask_question",
    "select_model",
    "use_gemini_tool",
    "list_conversations",
    "get_conversation",
    "select_conversation",
    "search_conversations",
    "get_library_stats",
    "list_sessions",
    "close_session",
    "get_health",
    "setup_auth",
  ],
  full: KNOWN_TOOL_NAMES,
};

export class SettingsManager {
  private readonly settingsPath: string;
  private settings: Settings;
  private readonly diagnostics: SettingsDiagnostic[] = [];

  constructor(settingsPath = path.join(CONFIG.configDir, "settings.json")) {
    this.settingsPath = settingsPath;
    this.settings = this.loadSettings();
  }

  private loadSettings(): Settings {
    try {
      mkdirSync(path.dirname(this.settingsPath), { recursive: true, mode: 0o700 });
      if (!existsSync(this.settingsPath)) {
        this.diagnostics.push({
          code: "SETTINGS_MISSING",
          message: "Settings file is absent; using the restricted standard profile.",
        });
        return cloneDefault();
      }
      return validateSettings(JSON.parse(readFileSync(this.settingsPath, "utf8")) as unknown);
    } catch (error) {
      const code = error instanceof SyntaxError || error instanceof SettingsValidationError
        ? "SETTINGS_INVALID"
        : "SETTINGS_UNREADABLE";
      const diagnostic: SettingsDiagnostic = {
        code,
        message: `${code}: using the restricted standard profile; repair ${path.basename(this.settingsPath)} before selecting full.`,
      };
      this.diagnostics.push(diagnostic);
      log.warning(diagnostic.message);
      return cloneDefault();
    }
  }

  async saveSettings(update: Partial<Settings>): Promise<void> {
    const candidate = validateSettings({ ...this.settings, ...update });
    await secureStorage.atomicWrite(this.settingsPath, `${JSON.stringify(candidate, null, 2)}\n`);
    this.settings = candidate;
  }

  getEffectiveSettings(environment: NodeJS.ProcessEnv = process.env): Settings {
    const envProfile = environment.CONVERSATIONLM_PROFILE;
    let profile = this.settings.profile;
    if (envProfile !== undefined) {
      if (isProfileName(envProfile)) {
        profile = envProfile;
      } else {
        profile = "standard";
        this.recordOnce({
          code: "ENV_PROFILE_INVALID",
          message: "Invalid CONVERSATIONLM_PROFILE; using the restricted standard profile.",
        });
      }
    }

    const disabledTools = new Set(this.settings.disabledTools);
    const envDisabled = environment.CONVERSATIONLM_DISABLED_TOOLS;
    if (envDisabled) {
      for (const name of envDisabled.split(",").map((value) => value.trim()).filter(Boolean)) {
        if (KNOWN_TOOLS.has(name)) disabledTools.add(name);
      }
    }
    return { profile, disabledTools: [...disabledTools], customSettings: this.settings.customSettings };
  }

  isToolAllowed(name: string, environment: NodeJS.ProcessEnv = process.env): boolean {
    if (!KNOWN_TOOLS.has(name)) return false;
    const { profile, disabledTools } = this.getEffectiveSettings(environment);
    return PROFILES[profile].includes(name) && !disabledTools.includes(name);
  }

  filterTools(allTools: Tool[], environment: NodeJS.ProcessEnv = process.env): Tool[] {
    return allTools.filter((tool) => this.isToolAllowed(tool.name, environment));
  }

  getSettingsPath(): string {
    return this.settingsPath;
  }

  getProfiles(): Readonly<Record<ProfileName, readonly string[]>> {
    return PROFILES;
  }

  getDiagnostics(): readonly SettingsDiagnostic[] {
    return [...this.diagnostics];
  }

  private recordOnce(diagnostic: SettingsDiagnostic): void {
    if (!this.diagnostics.some((entry) => entry.code === diagnostic.code)) {
      this.diagnostics.push(diagnostic);
      log.warning(diagnostic.message);
    }
  }
}

class SettingsValidationError extends Error {}

function validateSettings(value: unknown): Settings {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new SettingsValidationError("Settings must be an object");
  }
  const candidate = value as Record<string, unknown>;
  if (!isProfileName(candidate.profile)) throw new SettingsValidationError("Unknown profile");
  if (!Array.isArray(candidate.disabledTools) || !candidate.disabledTools.every((name) => typeof name === "string" && KNOWN_TOOLS.has(name))) {
    throw new SettingsValidationError("disabledTools must contain known tool names");
  }
  if (candidate.customSettings !== undefined && (!candidate.customSettings || typeof candidate.customSettings !== "object" || Array.isArray(candidate.customSettings))) {
    throw new SettingsValidationError("customSettings must be an object");
  }
  return {
    profile: candidate.profile,
    disabledTools: [...new Set(candidate.disabledTools)],
    ...(candidate.customSettings !== undefined && { customSettings: candidate.customSettings as Record<string, unknown> }),
  };
}

function isProfileName(value: unknown): value is ProfileName {
  return value === "minimal" || value === "standard" || value === "full";
}

function cloneDefault(): Settings {
  return { profile: DEFAULT_SETTINGS.profile, disabledTools: [] };
}
