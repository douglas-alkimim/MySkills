import type { SettingsManager } from "./settings-manager.js";

export interface ToolAuthorizationError {
  success: false;
  code: "TOOL_NOT_AUTHORIZED";
  error: string;
  tool: string;
  profile: string;
}

export class ToolAuthorizationPolicy {
  constructor(private readonly settings: SettingsManager) {}

  authorize(name: string): ToolAuthorizationError | null {
    if (this.settings.isToolAllowed(name)) return null;
    return {
      success: false,
      code: "TOOL_NOT_AUTHORIZED",
      error: `Tool '${name}' is not authorized by the active profile.`,
      tool: name,
      profile: this.settings.getEffectiveSettings().profile,
    };
  }
}
