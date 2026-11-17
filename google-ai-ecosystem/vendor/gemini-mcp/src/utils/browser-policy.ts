import { realpath } from "node:fs/promises";
import path from "node:path";
import type { Config } from "../config.js";

export class BrowserPolicy {
  launchOptions(config: Config, headless: boolean, storageState?: string) {
    return {
      headless,
      channel: "chrome" as const,
      viewport: config.viewport,
      locale: config.locale,
      timezoneId: config.timezoneId,
      ...(storageState && { storageState }),
      args: ["--disable-dev-shm-usage", "--no-first-run", "--no-default-browser-check"],
    };
  }

  async assertExistingDescendant(root: string, candidate: string): Promise<{ root: string; candidate: string }> {
    const [canonicalRoot, canonicalCandidate] = await Promise.all([realpath(root), realpath(candidate)]);
    const relative = path.relative(canonicalRoot, canonicalCandidate);
    if (relative === "" || relative.startsWith(`..${path.sep}`) || relative === ".." || path.isAbsolute(relative)) {
      throw new Error("Browser profile path is outside the managed instances root");
    }
    return { root: canonicalRoot, candidate: canonicalCandidate };
  }
}

export const browserPolicy = new BrowserPolicy();
