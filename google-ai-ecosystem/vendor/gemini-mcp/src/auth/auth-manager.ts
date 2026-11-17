/**
 * Authentication Manager for Gemini App
 *
 * Handles:
 * - Interactive login (headful browser for setup)
 * - Browser state persistence (cookies + localStorage + sessionStorage)
 * - Cookie expiry validation
 * - State expiry checks (24h file age)
 * - Hard reset for clean start
 *
 * Based on the Python implementation from auth.py
 */

import type { BrowserContext, Page } from "patchright";
import fs from "fs/promises";
import { existsSync } from "fs";
import path from "path";
import { CONFIG, GEMINI_AUTH_URL } from "../config.js";
import { log } from "../utils/logger.js";
import { browserPolicy } from "../utils/browser-policy.js";
import { secureStorage } from "../utils/secure-storage.js";
import { confirmationReceipts } from "../utils/confirmation-receipts.js";
import { createHash, randomBytes } from "node:crypto";
import type { ProgressCallback } from "../types.js";

/**
 * Critical cookie names for Google authentication
 */
const CRITICAL_COOKIE_NAMES = [
  "SID",
  "HSID",
  "SSID", // Google session
  "APISID",
  "SAPISID", // API auth
  "OSID",
  "__Secure-OSID", // Gemini App-specific
  "__Secure-1PSID",
  "__Secure-3PSID", // Secure variants
];

export type AuthStatus = "unconfigured" | "valid" | "repairable" | "expired" | "switch_requested" | "failed_recoverable";

interface AuthPaths {
  stateFilePath: string;
  sessionFilePath: string;
  browserStateDir: string;
  chromeProfileDir: string;
}

function isGeminiAppUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return (
      parsed.origin === "https://gemini.google.com" &&
      (parsed.pathname === "/app" || parsed.pathname.startsWith("/app/"))
    );
  } catch {
    return false;
  }
}

export class AuthManager {
  private stateFilePath: string;
  private sessionFilePath: string;
  private browserStateDir: string;
  private chromeProfileDir: string;
  private transientStatus: AuthStatus | null = null;
  private transientStatusExpiresAt = 0;

  constructor(paths: Partial<AuthPaths> = {}) {
    this.browserStateDir = paths.browserStateDir ?? CONFIG.browserStateDir;
    this.chromeProfileDir = paths.chromeProfileDir ?? CONFIG.chromeProfileDir;
    this.stateFilePath = paths.stateFilePath ?? path.join(this.browserStateDir, "state.json");
    this.sessionFilePath = paths.sessionFilePath ?? path.join(this.browserStateDir, "session.json");
  }

  // ============================================================================
  // Browser State Management
  // ============================================================================

  /**
   * Save entire browser state (cookies + localStorage)
   */
  async saveBrowserState(context: BrowserContext, page?: Page): Promise<boolean> {
    try {
      // Save storage state (cookies + localStorage + IndexedDB) atomically.
      const storageState = await context.storageState();
      await secureStorage.atomicWrite(this.stateFilePath, `${JSON.stringify(storageState, null, 2)}\n`);

      // Also save sessionStorage if page is provided
      if (page) {
        try {
          const sessionStorageData: string = await page.evaluate((): string => {
            // Properly extract sessionStorage as a plain object
            const storage: Record<string, string> = {};
            // @ts-expect-error - sessionStorage exists in browser context
            for (let i = 0; i < sessionStorage.length; i++) {
              // @ts-expect-error - sessionStorage exists in browser context
              const key = sessionStorage.key(i);
              if (key) {
                // @ts-expect-error - sessionStorage exists in browser context
                storage[key] = sessionStorage.getItem(key) || '';
              }
            }
            return JSON.stringify(storage);
          });

          await secureStorage.atomicWrite(this.sessionFilePath, sessionStorageData);

          const entries = Object.keys(JSON.parse(sessionStorageData)).length;
          log.success(`✅ Browser state saved (incl. sessionStorage: ${entries} entries)`);
        } catch (error) {
          log.warning(`⚠️  State saved, but sessionStorage failed: ${error}`);
        }
      } else {
        log.success("✅ Browser state saved");
      }

      return true;
    } catch (error) {
      log.error(`❌ Failed to save browser state: ${error}`);
      return false;
    }
  }

  /**
   * Check if saved browser state exists
   */
  async hasSavedState(): Promise<boolean> {
    try {
      await fs.access(this.stateFilePath);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get path to saved browser state
   */
  getStatePath(): string | null {
    // Synchronous check using imported existsSync
    if (existsSync(this.stateFilePath)) {
      return this.stateFilePath;
    }
    return null;
  }

  /**
   * Get the saved state path. Cookie validity is checked against the browser
   * after launch, so the state file's modification time is not an auth expiry.
   */
  async getValidStatePath(): Promise<string | null> {
    return this.getStatePath();
  }

  /**
   * Inspect the persisted state without launching Chrome.
   * Runtime requests use this to report a deterministic authentication state
   * while preserving the normal headless-only invariant.
   */
  async getAuthStatus(): Promise<AuthStatus> {
    if (this.transientStatus) {
      if (this.transientStatusExpiresAt === 0 || Date.now() < this.transientStatusExpiresAt) {
        return this.transientStatus;
      }
      this.transientStatus = null;
      this.transientStatusExpiresAt = 0;
    }
    if (!existsSync(this.stateFilePath)) {
      return "unconfigured";
    }

    try {
      const raw = await fs.readFile(this.stateFilePath, { encoding: "utf-8" });
      const state = JSON.parse(raw) as { cookies?: Array<{ name?: string; expires?: number }> };
      if (!Array.isArray(state.cookies)) {
        return "repairable";
      }

      const criticalCookies = state.cookies.filter(
        (cookie) => typeof cookie.name === "string" && CRITICAL_COOKIE_NAMES.includes(cookie.name)
      );
      if (criticalCookies.length === 0) {
        return "repairable";
      }

      const currentTime = Date.now() / 1000;
      const hasExpiredCookie = criticalCookies.some((cookie) => {
        const expires = cookie.expires ?? -1;
        return expires !== -1 && expires < currentTime;
      });
      return hasExpiredCookie ? "expired" : "valid";
    } catch {
      return "repairable";
    }
  }

  async getAuthStateVersion(): Promise<string> {
    const hash = createHash("sha256");
    for (const file of [this.stateFilePath, this.sessionFilePath]) {
      try {
        const info = await fs.stat(file);
        hash.update(`${path.basename(file)}:${info.size}:${info.mtimeMs}`);
      } catch (error) {
        if (!isMissing(error)) throw error;
        hash.update(`${path.basename(file)}:missing`);
      }
    }
    try {
      const info = await fs.stat(this.chromeProfileDir);
      hash.update(`profile:${info.size}:${info.mtimeMs}`);
    } catch (error) {
      if (!isMissing(error)) throw error;
      hash.update("profile:missing");
    }
    return hash.digest("hex");
  }

  async previewAccountSwitch(): Promise<{ receipt: string; expiresAt: string; resources: string[]; stateVersion: string }> {
    const resources = [this.stateFilePath, this.sessionFilePath, this.chromeProfileDir].map((entry) => path.resolve(entry));
    const stateVersion = await this.getAuthStateVersion();
    const issued = confirmationReceipts.issue("switch_google_account", resources, stateVersion);
    this.transientStatus = "switch_requested";
    this.transientStatusExpiresAt = Date.parse(issued.expiresAt);
    return { ...issued, resources, stateVersion };
  }

  async consumeAccountSwitchReceipt(receipt: string): Promise<void> {
    const resources = [this.stateFilePath, this.sessionFilePath, this.chromeProfileDir].map((entry) => path.resolve(entry));
    const stateVersion = await this.getAuthStateVersion();
    confirmationReceipts.consume(receipt, "switch_google_account", resources, stateVersion);
    this.transientStatus = null;
    this.transientStatusExpiresAt = 0;
  }

  async performAccountSwitch(
    receipt: string,
    sendProgress?: ProgressCallback,
    overrideHeadless?: boolean,
  ): Promise<boolean> {
    await this.consumeAccountSwitchReceipt(receipt);
    const recovery = await this.createRecoverySnapshot();
    try {
      await this.clearAllAuthData();
      const success = await this.performSetup(sendProgress, overrideHeadless);
      if (!success) {
        await this.restoreRecoverySnapshot(recovery);
        this.transientStatus = "failed_recoverable";
        this.transientStatusExpiresAt = 0;
        return false;
      }
      await this.discardRecoverySnapshot(recovery);
      this.transientStatus = null;
      this.transientStatusExpiresAt = 0;
      return true;
    } catch (error) {
      await this.restoreRecoverySnapshot(recovery);
      this.transientStatus = "failed_recoverable";
      this.transientStatusExpiresAt = 0;
      throw error;
    }
  }

  /**
   * Load sessionStorage from file
   */
  async loadSessionStorage(): Promise<Record<string, string> | null> {
    try {
      const data = await fs.readFile(this.sessionFilePath, { encoding: "utf-8" });
      const sessionData = JSON.parse(data);
      log.success(`✅ Loaded sessionStorage (${Object.keys(sessionData).length} entries)`);
      return sessionData;
    } catch (error) {
      log.warning(`⚠️  Failed to load sessionStorage: ${error}`);
      return null;
    }
  }

  // ============================================================================
  // Cookie Validation
  // ============================================================================

  /**
   * Validate if saved state is still valid
   */
  async validateState(context: BrowserContext): Promise<boolean> {
    try {
      const cookies = await context.cookies();
      if (cookies.length === 0) {
        log.warning("⚠️  No cookies found in state");
        return false;
      }

      // Check for Google auth cookies
      const googleCookies = cookies.filter((c) =>
        c.domain.includes("google.com")
      );
      if (googleCookies.length === 0) {
        log.warning("⚠️  No Google cookies found");
        return false;
      }

      // Check if important cookies are expired
      const currentTime = Date.now() / 1000;

      for (const cookie of googleCookies) {
        const expires = cookie.expires ?? -1;
        if (expires !== -1 && expires < currentTime) {
          log.warning(`⚠️  Cookie '${cookie.name}' has expired`);
          return false;
        }
      }

      log.success("✅ State validation passed");
      return true;
    } catch (error) {
      log.warning(`⚠️  State validation failed: ${error}`);
      return false;
    }
  }

  /**
   * Validate if critical authentication cookies are still valid
   */
  async validateCookiesExpiry(context: BrowserContext): Promise<boolean> {
    try {
      const cookies = await context.cookies();
      if (cookies.length === 0) {
        log.warning("⚠️  No cookies found");
        return false;
      }

      // Find critical cookies
      const criticalCookies = cookies.filter((c) =>
        CRITICAL_COOKIE_NAMES.includes(c.name)
      );

      if (criticalCookies.length === 0) {
        log.warning("⚠️  No critical auth cookies found");
        return false;
      }

      // Check expiration for each critical cookie
      const currentTime = Date.now() / 1000;
      const expiredCookies: string[] = [];

      for (const cookie of criticalCookies) {
        const expires = cookie.expires ?? -1;

        // -1 means session cookie (valid until browser closes)
        if (expires === -1) {
          continue;
        }

        // Check if cookie is expired
        if (expires < currentTime) {
          expiredCookies.push(cookie.name);
        }
      }

      if (expiredCookies.length > 0) {
        log.warning(`⚠️  Expired cookies: ${expiredCookies.join(", ")}`);
        return false;
      }

      log.success(`✅ All ${criticalCookies.length} critical cookies are valid`);
      return true;
    } catch (error) {
      log.warning(`⚠️  Cookie validation failed: ${error}`);
      return false;
    }
  }

  // ============================================================================
  // Interactive Login
  // ============================================================================

  /**
   * Perform interactive login
   * User will see a browser window and login manually
   *
   * SIMPLE & RELIABLE: Just wait for URL to change to gemini.google.com/app
   */
  async performLogin(page: Page, sendProgress?: ProgressCallback): Promise<boolean> {
    try {
      log.info("🌐 Opening Google login page...");
      log.warning("📝 Please login to your Google account");
      log.warning("⏳ Browser will close automatically once you reach Gemini App");
      log.info("");

      // Progress: Navigating
      await sendProgress?.("Navigating to Google login...", 3, 10);

      // Navigate to Google login (redirects to Gemini App after auth)
      await page.goto(GEMINI_AUTH_URL, { timeout: 60000 });

      // Progress: Waiting for login
      await sendProgress?.("Waiting for manual login (up to 10 minutes)...", 4, 10);

      // Wait for user to complete login
      log.warning("⏳ Waiting for login (up to 10 minutes)...");

      const checkIntervalMs = 1000; // Check every 1 second
      const maxAttempts = 600; // 10 minutes total
      let lastProgressUpdate = 0;

      for (let attempt = 0; attempt < maxAttempts; attempt++) {
        try {
          const currentUrl = page.url();
          const elapsedSeconds = Math.floor(attempt * (checkIntervalMs / 1000));

          // Send progress every 10 seconds
          if (elapsedSeconds - lastProgressUpdate >= 10) {
            lastProgressUpdate = elapsedSeconds;
            const progressStep = Math.min(8, 4 + Math.floor(elapsedSeconds / 60));
            await sendProgress?.(
              `Waiting for login... (${elapsedSeconds}s elapsed)`,
              progressStep,
              10
            );
          }

          // ✅ SIMPLE: Check if we're on Gemini App (any path!)
          if (isGeminiAppUrl(currentUrl)) {
            await sendProgress?.("Login successful! Gemini App detected!", 9, 10);
            log.success("✅ Login successful! Gemini App URL detected.");
            log.success(`✅ Current URL: ${currentUrl}`);

            // Short wait to ensure page is loaded
            await page.waitForTimeout(2000);
            return true;
          }

          // Still on accounts.google.com - log periodically
          if (currentUrl.includes("accounts.google.com") && attempt % 30 === 0 && attempt > 0) {
            log.warning(`⏳ Still waiting... (${elapsedSeconds}s elapsed)`);
          }

          await page.waitForTimeout(checkIntervalMs);
        } catch {
          await page.waitForTimeout(checkIntervalMs);
          continue;
        }
      }

      // Timeout reached - final check
      const currentUrl = page.url();
      if (isGeminiAppUrl(currentUrl)) {
        await sendProgress?.("Login successful (detected on timeout check)!", 9, 10);
        log.success("✅ Login successful (detected on timeout check)");
        return true;
      }

      log.error("❌ Login verification failed - timeout reached");
      log.warning(`Current URL: ${currentUrl}`);
      return false;
    } catch (error) {
      log.error(`❌ Login failed: ${error}`);
      return false;
    }
  }

  // ============================================================================
  // Additional Helper Methods
  // ============================================================================

  /**
   * Load authentication state from a specific file path
   */
  async loadAuthState(context: BrowserContext, statePath: string): Promise<boolean> {
    try {
      // Read state.json
      const stateData = await fs.readFile(statePath, { encoding: "utf-8" });
      const state = JSON.parse(stateData);

      // Add cookies to context
      if (state.cookies) {
        await context.addCookies(state.cookies);
        log.success(`✅ Loaded ${state.cookies.length} cookies from ${statePath}`);
        return true;
      }

      log.warning(`⚠️  No cookies found in state file`);
      return false;
    } catch (error) {
      log.error(`❌ Failed to load auth state: ${error}`);
      return false;
    }
  }

  /**
   * Perform interactive setup (for setup_auth tool)
   * Opens a PERSISTENT browser for manual login
   *
   * CRITICAL: Uses the SAME persistent context as runtime!
   * This ensures cookies are automatically saved to the Chrome profile.
   *
   * Benefits over temporary browser:
   * - Session cookies persist correctly (Playwright bug workaround)
   * - Same MCP-owned profile as runtime
   * - No need for addCookies() workarounds
   * - Automatic cookie persistence via Chrome profile
   *
   * @param sendProgress Optional progress callback
   * @param overrideHeadless Optional override for headless mode (true = visible, false = headless)
   *                         If not provided, defaults to true (visible) for setup
   */
  async performSetup(sendProgress?: ProgressCallback, overrideHeadless?: boolean): Promise<boolean> {
    const { chromium } = await import("patchright");

    // Determine headless mode: override or default to true (visible for setup)
    // overrideHeadless contains show_browser value (true = show, false = hide)
    const shouldShowBrowser = overrideHeadless !== undefined ? overrideHeadless : true;

    if ((await this.getAuthStatus()) === "valid") {
      log.info("Authentication is already valid; preserving the active profile");
      return true;
    }

    const recovery = await this.createRecoverySnapshot();
    try {
      log.info("🔄 Preparing a recoverable authentication attempt...");
      await sendProgress?.("Creating a recoverable authentication snapshot...", 1, 10);

      log.info("🚀 Launching persistent browser for interactive setup...");
      log.info(`  📍 Profile: ${this.chromeProfileDir}`);
      await sendProgress?.("Launching persistent browser...", 2, 10);

      // ✅ CRITICAL FIX: Use launchPersistentContext (same as runtime!)
      // This ensures session cookies persist correctly
      const context = await chromium.launchPersistentContext(
        this.chromeProfileDir,
        browserPolicy.launchOptions(CONFIG, !shouldShowBrowser)
      );

      // Get or create a page
      const pages = context.pages();
      const page = pages.length > 0 ? pages[0] : await context.newPage();

      // Perform login with progress updates
      const loginSuccess = await this.performLogin(page, sendProgress);

      if (loginSuccess) {
        // ✅ Save browser state to state.json (for validation & backup)
        // Chrome ALSO saves everything to the persistent profile automatically!
        await sendProgress?.("Saving authentication state...", 9, 10);
        await this.saveBrowserState(context, page);
        log.success("✅ Setup complete - authentication saved to:");
        log.success(`  📄 State file: ${this.stateFilePath}`);
        log.success(`  📁 Chrome profile: ${this.chromeProfileDir}`);
        log.info("💡 Session cookies will now persist across restarts!");
      }

      // Close persistent context
      await context.close();

      if (loginSuccess) {
        await this.discardRecoverySnapshot(recovery);
        this.transientStatus = null;
        this.transientStatusExpiresAt = 0;
        return true;
      }
      await this.restoreRecoverySnapshot(recovery);
      this.transientStatus = "failed_recoverable";
      this.transientStatusExpiresAt = 0;
      return false;
    } catch (error) {
      log.error(`❌ Setup failed: ${error}`);
      await this.restoreRecoverySnapshot(recovery).catch((restoreError) => {
        log.error(`Authentication recovery failed: ${restoreError}`);
      });
      this.transientStatus = "failed_recoverable";
      this.transientStatusExpiresAt = 0;
      return false;
    }
  }

  private async createRecoverySnapshot(): Promise<string> {
    const recovery = path.join(this.browserStateDir, `.recovery-${randomBytes(8).toString("hex")}`);
    await fs.mkdir(recovery, { recursive: true, mode: 0o700 });
    for (const [source, name] of [
      [this.stateFilePath, "state.json"],
      [this.sessionFilePath, "session.json"],
    ] as const) {
      if (existsSync(source)) await fs.copyFile(source, path.join(recovery, name));
    }
    if (existsSync(this.chromeProfileDir)) {
      await fs.cp(this.chromeProfileDir, path.join(recovery, "chrome_profile"), { recursive: true, force: false });
    }
    return recovery;
  }

  private async restoreRecoverySnapshot(recovery: string): Promise<void> {
    await fs.rm(this.stateFilePath, { force: true });
    await fs.rm(this.sessionFilePath, { force: true });
    await fs.rm(this.chromeProfileDir, { recursive: true, force: true });
    for (const [name, target] of [
      ["state.json", this.stateFilePath],
      ["session.json", this.sessionFilePath],
    ] as const) {
      const source = path.join(recovery, name);
      if (existsSync(source)) {
        await secureStorage.atomicWrite(target, await fs.readFile(source));
      }
    }
    const profileBackup = path.join(recovery, "chrome_profile");
    if (existsSync(profileBackup)) {
      await fs.cp(profileBackup, this.chromeProfileDir, { recursive: true, force: false });
    }
    await this.discardRecoverySnapshot(recovery);
  }

  private async discardRecoverySnapshot(recovery: string): Promise<void> {
    await fs.rm(recovery, { recursive: true, force: true });
  }

  // ============================================================================
  // Cleanup
  // ============================================================================

  /**
   * Clear ALL authentication data for account switching
   *
   * CRITICAL: This deletes EVERYTHING to ensure only ONE account is active:
   * - All state.json files (cookies, localStorage)
   * - sessionStorage files
   * - MCP-owned Chrome profile directory
   *
   * Use this BEFORE authenticating a new account!
   */
  async clearAllAuthData(): Promise<void> {
    log.warning("🗑️  Clearing ALL authentication data for account switch...");

    let deletedCount = 0;

    // Delete only the exact resources bound to the reviewed switch receipt.
    // Any unexpected I/O error aborts the transaction so the caller can roll
    // back from its recovery snapshot.
    for (const file of [this.stateFilePath, this.sessionFilePath]) {
      try {
        await fs.unlink(file);
        log.info(`  ✅ Deleted: ${path.basename(file)}`);
        deletedCount++;
      } catch (error) {
        if (!isMissing(error)) throw error;
      }
    }

    // Delete Chrome profile (THE KEY for account switching!)
    // This removes the MCP-owned browser profile for an explicit account switch.
    const chromeProfileDir = this.chromeProfileDir;
    if (existsSync(chromeProfileDir)) {
      await fs.rm(chromeProfileDir, { recursive: true, force: false });
      log.success(`  ✅ Deleted Chrome profile: ${chromeProfileDir}`);
      deletedCount++;
    }

    if (deletedCount === 0) {
      log.info("  ℹ️  No old auth data found (already clean)");
    } else {
      log.success(`✅ All auth data cleared (${deletedCount} items) - ready for new account!`);
    }
  }

  /**
   * Clear all saved authentication state
   */
  async clearState(): Promise<boolean> {
    try {
      try {
        await fs.unlink(this.stateFilePath);
      } catch {
        // File doesn't exist
      }

      try {
        await fs.unlink(this.sessionFilePath);
      } catch {
        // File doesn't exist
      }

      log.success("✅ Authentication state cleared");
      return true;
    } catch (error) {
      log.error(`❌ Failed to clear state: ${error}`);
      return false;
    }
  }

  /**
   * HARD RESET: Completely delete ALL authentication state
   */
  async hardResetState(): Promise<boolean> {
    try {
      log.warning("🧹 Performing HARD RESET of all authentication state...");

      let deletedCount = 0;

      // Delete state file
      try {
        await fs.unlink(this.stateFilePath);
        log.info(`  🗑️  Deleted: ${this.stateFilePath}`);
        deletedCount++;
      } catch {
        // File doesn't exist
      }

      // Delete session file
      try {
        await fs.unlink(this.sessionFilePath);
        log.info(`  🗑️  Deleted: ${this.sessionFilePath}`);
        deletedCount++;
      } catch {
        // File doesn't exist
      }

      // Delete entire browser_state_dir
      try {
        const files = await fs.readdir(this.browserStateDir);
        for (const file of files) {
          await fs.unlink(path.join(this.browserStateDir, file));
          deletedCount++;
        }
        log.info(`  🗑️  Deleted browser-state files (${files.length})`);
      } catch {
        // Directory doesn't exist or empty
      }

      if (deletedCount === 0) {
        log.info("  ℹ️  No state to delete (already clean)");
      } else {
        log.success(`✅ Hard reset complete: ${deletedCount} items deleted`);
      }

      return true;
    } catch (error) {
      log.error(`❌ Hard reset failed: ${error}`);
      return false;
    }
  }
}

function isMissing(error: unknown): boolean {
  return typeof error === "object" && error !== null && "code" in error && error.code === "ENOENT";
}
