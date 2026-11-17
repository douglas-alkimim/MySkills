/**
 * Browser Session
 *
 * Represents a single browser session for Gemini interactions.
 *
 * Features:
 * - Deterministic question input
 * - Streaming response detection
 * - Auto-login on session expiry
 * - Session activity tracking
 * - Chat history reset
 *
 * Based on the Python implementation from browser_session.py
 */

import type { BrowserContext, Page } from "patchright";
import { SharedContextManager } from "./shared-context-manager.js";
import { AuthManager } from "../auth/auth-manager.js";
import { fillDeterministically, settleDelay } from "../utils/interaction-utils.js";
import {
  waitForLatestAnswer,
  snapshotAllResponses,
} from "../utils/page-utils.js";
import { CONFIG } from "../config.js";
import { log } from "../utils/logger.js";
import type { SessionInfo, ProgressCallback } from "../types.js";
import { AuthenticationRequiredError, RateLimitError } from "../errors.js";

export class BrowserSession {
  public readonly sessionId: string;
  public readonly geminiUrl: string;
  public readonly createdAt: number;
  public lastActivity: number;
  public messageCount: number;

  private context!: BrowserContext;
  private sharedContextManager: SharedContextManager;
  private authManager: AuthManager;
  private page: Page | null = null;
  private initialized: boolean = false;

  constructor(
    sessionId: string,
    sharedContextManager: SharedContextManager,
    authManager: AuthManager,
    geminiUrl: string
  ) {
    this.sessionId = sessionId;
    this.sharedContextManager = sharedContextManager;
    this.authManager = authManager;
    this.geminiUrl = geminiUrl;
    this.createdAt = Date.now();
    this.lastActivity = Date.now();
    this.messageCount = 0;

    log.info(`🆕 BrowserSession ${sessionId} created`);
  }

  /**
   * Initialize the session by creating a page and navigating to the conversation
   */
  async init(): Promise<void> {
    if (this.initialized) {
      log.warning(`⚠️  Session ${this.sessionId} already initialized`);
      return;
    }

    log.info(`🚀 Initializing session ${this.sessionId}...`);

    try {
      // Ensure a valid shared context
      this.context = await this.sharedContextManager.getOrCreateContext();

      // Create new page (tab) in the shared context (with auto-recovery)
      try {
        this.page = await this.context.newPage();
      } catch (e: any) {
        const msg = String(e?.message || e);
        if (/has been closed|Target .* closed|Browser has been closed|Context .* closed/i.test(msg)) {
          log.warning("  ♻️  Context was closed. Recreating and retrying newPage...");
          this.context = await this.sharedContextManager.getOrCreateContext();
          this.page = await this.context.newPage();
        } else {
          throw e;
        }
      }
      log.success(`  ✅ Created new page`);

      // Navigate to conversation
      log.info(`  🌐 Navigating to: ${this.geminiUrl}`);
      await this.page.goto(this.geminiUrl, {
        waitUntil: "domcontentloaded",
        timeout: CONFIG.browserTimeout,
      });

      // Wait for page to stabilize
      await settleDelay(2000);

      // Check if we need to login
      const isAuthenticated = await this.authManager.validateCookiesExpiry(
        this.context
      );

      if (!isAuthenticated) {
        log.warning(`  🔑 Session ${this.sessionId} needs authentication`);
        const loginSuccess = await this.ensureAuthenticated();
        if (!loginSuccess) {
          throw new AuthenticationRequiredError();
        }
      } else {
        log.success(`  ✅ Session already authenticated`);
      }

      // CRITICAL: Restore sessionStorage from saved state
      // This is essential for maintaining Google session state!
      log.info(`  🔄 Restoring sessionStorage...`);
      const sessionData = await this.authManager.loadSessionStorage();
      if (sessionData) {
        const entryCount = Object.keys(sessionData).length;
        if (entryCount > 0) {
          await this.restoreSessionStorage(sessionData, entryCount);
        } else {
          log.info(`  ℹ️  SessionStorage empty (fresh session)`);
        }
      } else {
        log.info(`  ℹ️  No saved sessionStorage found (fresh session)`);
      }

      // Wait for Gemini interface to load
      log.info(`  ⏳ Waiting for Gemini interface...`);
      await this.waitForGeminiAppReady();

      this.initialized = true;
      this.updateActivity();
      log.success(`✅ Session ${this.sessionId} initialized successfully`);
    } catch (error) {
      log.error(`❌ Failed to initialize session ${this.sessionId}: ${error}`);
      if (this.page) {
        await this.page.close();
        this.page = null;
      }
      throw error;
    }
  }

  /**
   * Wait for Gemini interface to be ready
   *
   * IMPORTANT: Matches Python implementation EXACTLY!
   * - Uses SPECIFIC selectors (div[contenteditable=\"true\"])
   * - Checks ONLY for "visible" state (NOT disabled!)
   * - NO placeholder checks (let Gemini handle that!)
   *
   * Based on Python _wait_for_ready() from browser_session.py:104-113
   */
  private async waitForGeminiAppReady(): Promise<void> {
    if (!this.page) {
      throw new Error("Page not initialized");
    }

    try {
      // PRIMARY: Exact Python selector - div[contenteditable=\"true\"]
      log.info("  ⏳ Waiting for chat input (div[contenteditable=\"true\"])...");
      await this.page.waitForSelector("div[contenteditable=\"true\"]", {
        timeout: 10000, // Python uses 10s timeout
        state: "visible", // ONLY check visibility (NO disabled check!)
      });
      log.success("  ✅ Chat input ready!");
    } catch {
      // FALLBACK: Python alternative selector
      try {
        log.info("  ⏳ Trying fallback selector (aria-label)...");
        await this.page.waitForSelector('textarea[aria-label="Feld für Anfragen"]', {
          timeout: 5000, // Python uses 5s for fallback
          state: "visible",
        });
        log.success("  ✅ Chat input ready (fallback)!");
      } catch (error) {
        log.error(`  ❌ Gemini interface not ready: ${error}`);
        throw new Error(
          "Could not find Gemini chat input. " +
          "Please ensure the conversation page has loaded correctly."
        );
      }
    }
  }

  private isPageClosedSafe(): boolean {
    if (!this.page) return true;
    const p: any = this.page as any;
    try {
      if (typeof p.isClosed === 'function') {
        if (p.isClosed()) return true;
      }
      // Accessing URL should be safe; if page is gone, this may throw
      void this.page.url();
      return false;
    } catch {
      return true;
    }
  }

  /** Ensure the session uses a valid persisted state from manual setup. */
  private async ensureAuthenticated(): Promise<boolean> {
    if (!this.page) {
      throw new Error("Page not initialized");
    }

    log.info(`🔑 Checking authentication for session ${this.sessionId}...`);

    // Check cookie validity
    const isValid = await this.authManager.validateCookiesExpiry(this.context);

    if (isValid) {
      log.success(`  ✅ Cookies valid`);
      return true;
    }

    log.warning(`  ⚠️  Cookies expired or invalid`);

    // Try to get valid auth state
    const statePath = await this.authManager.getValidStatePath();

    if (statePath) {
      // Load saved state
      log.info(`  📂 Loading auth state from: ${statePath}`);
      await this.authManager.loadAuthState(this.context, statePath);

      // Reload page to apply new auth
      log.info(`  🔄 Reloading page...`);
      await (this.page as Page).reload({ waitUntil: "domcontentloaded" });
      await settleDelay(2000);

      // Check if it worked
      const nowValid = await this.authManager.validateCookiesExpiry(
        this.context
      );
      if (nowValid) {
        log.success(`  ✅ Auth state loaded successfully`);
        return true;
      }
    }

    // Need fresh login
    log.warning(`  🔑 Fresh login required`);

    log.error(
      `  ❌ Manual login required. Call setup_auth(show_browser=true), finish Google login, close the browser, and retry.`
    );
    return false;
  }

  private getOriginFromUrl(url: string): string | null {
    try {
      return new URL(url).origin;
    } catch {
      return null;
    }
  }

  /**
   * Safely restore sessionStorage when the page is on the expected origin
   */
  private async restoreSessionStorage(
    sessionData: Record<string, string>,
    entryCount: number
  ): Promise<void> {
    if (!this.page) {
      log.warning(`  ⚠️  Cannot restore sessionStorage without an active page`);
      return;
    }

    const targetOrigin = this.getOriginFromUrl(this.geminiUrl);
    if (!targetOrigin) {
      log.warning(`  ⚠️  Unable to determine target origin for sessionStorage restore`);
      return;
    }

    let restored = false;

    const applyToPage = async (): Promise<boolean> => {
      if (!this.page) {
        return false;
      }

      const currentOrigin = this.getOriginFromUrl(this.page.url());
      if (currentOrigin !== targetOrigin) {
        return false;
      }

      try {
        await this.page.evaluate((data) => {
          for (const [key, value] of Object.entries(data)) {
            // @ts-expect-error - sessionStorage exists in browser context
            sessionStorage.setItem(key, value);
          }
        }, sessionData);
        restored = true;
        log.success(`  ✅ SessionStorage restored: ${entryCount} entries`);
        return true;
      } catch (error) {
        log.warning(`  ⚠️  Failed to restore sessionStorage: ${error}`);
        return false;
      }
    };

    if (await applyToPage()) {
      return;
    }

    log.info(`  ⏳ Waiting for Gemini origin before restoring sessionStorage...`);

    const handleNavigation = async () => {
      if (restored) {
        return;
      }

      if (await applyToPage()) {
        this.page?.off("framenavigated", handleNavigation);
      }
    };

    this.page.on("framenavigated", handleNavigation);
  }

  /**
   * Ask a question to Gemini
   */
  async ask(
    question: string,
    sendProgress?: ProgressCallback,
    timeoutMs: number = 120000,
    preserveActiveMode: boolean = false
  ): Promise<string> {
    const askOnce = async (): Promise<string> => {
      if (!this.initialized || !this.page || this.isPageClosedSafe()) {
        log.warning(`  ℹ️  Session not initialized or page missing → re-initializing...`);
        await this.init();
      }

      log.info(`💬 [${this.sessionId}] Asking: "${question.substring(0, 100)}..."`);
      const page = this.page!;
      // Ensure we're still authenticated
      await sendProgress?.("Verifying authentication...", 2, 5);
      const isAuth = await this.authManager.validateCookiesExpiry(this.context);
      if (!isAuth) {
        log.warning(`  🔑 Session expired, re-authenticating...`);
        await sendProgress?.("Re-authenticating session...", 2, 5);
        const reAuthSuccess = await this.ensureAuthenticated();
        if (!reAuthSuccess) {
          throw new Error("Failed to re-authenticate session");
        }
      }

      if (!preserveActiveMode) {
        await this.clearActiveSpecialModes();
      }

      // Snapshot existing responses BEFORE asking
      log.info(`  📸 Snapshotting existing responses...`);
      const existingResponses = await snapshotAllResponses(page);
      log.success(`  ✅ Captured ${existingResponses.length} existing responses`);

      // Find the chat input
      const inputSelector = await this.findChatInput();
      if (!inputSelector) {
        throw new Error(
          "Could not find visible chat input element. " +
          "Please check if the conversation page has loaded correctly."
        );
      }

      log.info(`  ⌨️  Filling question input...`);
      await sendProgress?.("Filling question input...", 2, 5);
      await fillDeterministically(page, inputSelector, question);

      // Small pause before submitting
      await settleDelay(500);

      // Submit the question (Enter key)
      log.info(`  📤 Submitting question...`);
      await sendProgress?.("Submitting question...", 3, 5);
      await page.keyboard.press("Enter");

      // Small pause after submit
      await settleDelay(1000);

      // Wait for the response with streaming detection
      log.info(`  ⏳ Waiting for response (with streaming detection)...`);
      await sendProgress?.("Waiting for Gemini response (streaming detection active)...", 3, 5);
      const answer = await waitForLatestAnswer(page, {
        question,
        timeoutMs,
        pollIntervalMs: 1000,
        ignoreTexts: existingResponses,
        debug: false,
      });

      if (!answer) {
        const diagnostics = await this.getResponseDiagnostics(question);
        throw new Error(
          `Timeout waiting for response from Gemini. Page diagnostics: ${diagnostics}`
        );
      }

      // Check for rate limit errors AFTER receiving answer
      log.info(`  🔍 Checking for rate limit errors...`);
      if (await this.detectRateLimitError()) {
        throw new RateLimitError("Gemini displayed a quota or capacity limit for the current request");
      }

      // Update session stats
      this.messageCount++;
      this.updateActivity();

      log.success(
        `✅ [${this.sessionId}] Received answer (${answer.length} chars, ${this.messageCount} total messages)`
      );

      return answer;
    };

    try {
      return await askOnce();
    } catch (error: any) {
      const msg = String(error?.message || error);
      if (/has been closed|Target .* closed|Browser has been closed|Context .* closed/i.test(msg)) {
        log.warning(`  ♻️  Detected closed page/context. Recovering session and retrying ask...`);
        try {
          this.initialized = false;
          if (this.page) { try { await this.page.close(); } catch {} }
          this.page = null;
          await this.init();
          return await askOnce();
        } catch (e2) {
          log.error(`❌ Recovery failed: ${e2}`);
          throw e2;
        }
      }
      log.error(`❌ [${this.sessionId}] Failed to ask question: ${msg}`);
      throw error;
    }
  }

  /**
   * Find the chat input element
   *
   * IMPORTANT: Matches Python implementation EXACTLY!
   * - Uses SPECIFIC selectors from Python
   * - Checks ONLY visibility (NOT disabled state!)
   *
   * Based on Python ask() method from browser_session.py:166-171
   */
  private async findChatInput(): Promise<string | null> {
    if (!this.page) {
      return null;
    }

    // Use EXACT Python selectors (in order of preference)
    const selectors = [
      'div[contenteditable="true"][aria-label*="comando" i]',
      'div[role="textbox"][contenteditable="true"]',
      "div[contenteditable=\"true\"]",
      'textarea[aria-label="Feld für Anfragen"]',
      'textarea[aria-label*="prompt" i]',
    ];

    for (const selector of selectors) {
      try {
        const element = await this.page.$(selector);
        if (element) {
          const isVisible = await element.isVisible();
          if (isVisible) {
            // NO disabled check! Just like Python!
            log.success(`  ✅ Found chat input: ${selector}`);
            return selector;
          }
        }
      } catch {
        continue;
      }
    }

    log.error(`  ❌ Could not find visible chat input`);
    return null;
  }

  private async clearActiveSpecialModes(): Promise<void> {
    if (!this.page) return;

    const selectors = [
      'button[aria-label^="Desmarcar "]',
      'button[aria-label^="Remover "]',
      'button[aria-label^="Deselect "]',
      'button[aria-label^="Remove "]',
      'button:has-text("Deep Research")',
      'button:has-text("Pesquisa aprofundada")',
      'button:has-text("Pesquisa detalhada")',
      'button:has-text("Vídeos")',
      'button:has-text("Create video")',
      'button:has-text("Imagens")',
      'button:has-text("Create image")',
    ];

    for (let attempt = 0; attempt < 5; attempt++) {
      let cleared = false;
      for (const selector of selectors) {
        const candidates = this.page.locator(selector);
        const count = await candidates.count();
        for (let index = 0; index < count; index++) {
          const candidate = candidates.nth(index);
          if (await candidate.isVisible()) {
            const label =
              (await candidate.getAttribute("aria-label")) ||
              (await candidate.innerText().catch(() => ""));
            log.info(`  🧹 Clearing active Gemini mode: ${label || selector}`);
            await candidate.click();
            await settleDelay(250);
            cleared = true;
            break;
          }
        }
        if (cleared) break;
      }
      if (!cleared) {
        return;
      }
    }
  }

  /**
   * Return a compact, text-only DOM summary through the MCP response when the
   * web UI changes and the normal response selectors no longer match.
   */
  private async getResponseDiagnostics(question: string): Promise<string> {
    if (!this.page) {
      return JSON.stringify({ error: "page-not-initialized" });
    }

    try {
      return JSON.stringify(
        await this.page.evaluate((submittedQuestion) => {
          const browserGlobal: any = globalThis as any;
          const document: any = browserGlobal.document;
          const normalize = (value: string | null | undefined) =>
            (value || "").trim().replace(/\s+/g, " ");
          const isVisible = (element: any) => {
            const rect = element.getBoundingClientRect();
            const style = browserGlobal.getComputedStyle(element);
            return (
              rect.width > 0 &&
              rect.height > 0 &&
              style.display !== "none" &&
              style.visibility !== "hidden"
            );
          };
          const bodyText = normalize(document.body?.innerText);
          const responseHints = Array.from(
            document.querySelectorAll(
              ".model-response-text, .markdown-main-panel, message-content, " +
              "model-response, [class*='model-response'], [class*='response']"
            )
          )
            .filter(isVisible)
            .map((element: any) => ({
              tag: element.tagName.toLowerCase(),
              className: normalize(element.getAttribute("class")),
              text: normalize(element.innerText).slice(0, 500),
            }))
            .filter((entry) => entry.text && entry.text !== normalize(submittedQuestion))
            .slice(-20);

          const leafText = Array.from(document.querySelectorAll("p, span, div"))
            .filter(
              (element: any) =>
                isVisible(element) &&
                element.children.length === 0 &&
                normalize(element.textContent).length > 0
            )
            .map((element: any) => ({
              tag: element.tagName.toLowerCase(),
              className: normalize(element.getAttribute("class")),
              text: normalize(element.textContent).slice(0, 300),
            }))
            .filter((entry) => entry.text !== normalize(submittedQuestion))
            .slice(-30);

          return {
            url: browserGlobal.location.href,
            title: document.title,
            bodyTail: bodyText.slice(-1500),
            responseHints,
            leafText,
          };
        }, question)
      ).slice(0, 16_000);
    } catch (error) {
      return JSON.stringify({ error: String(error) });
    }
  }

  /**
   * Detect if a rate limit error occurred
   *
   * Searches the page for observed rate limit/quota messages without assuming
   * a plan, fixed limit, reset time or workaround.
   *
   * @returns true if rate limit error detected, false otherwise
   */
  private async detectRateLimitError(): Promise<boolean> {
    if (!this.page) {
      return false;
    }

    // Error message selectors (common patterns for error containers)
    const errorSelectors = [
      ".error-message",
      ".error-container",
      "[role='alert']",
      ".rate-limit-message",
      "[data-error]",
      ".notification-error",
      ".alert-error",
      ".toast-error",
    ];

    // Keywords that indicate rate limiting
    const keywords = [
      "rate limit",
      "limit exceeded",
      "quota exhausted",
      "daily limit",
      "limit reached",
      "too many requests",
      "ratenlimit",
      "quota",
      "query limit",
      "request limit",
    ];

    // Check error containers for rate limit messages
    for (const selector of errorSelectors) {
      try {
        const elements = await this.page.$$(selector);
        for (const el of elements) {
          try {
            const text = await el.innerText();
            const lower = text.toLowerCase();

            if (keywords.some((k) => lower.includes(k))) {
              log.error(`🚫 Rate limit detected: ${text.slice(0, 100)}`);
              return true;
            }
          } catch {
            continue;
          }
        }
      } catch {
        continue;
      }
    }

    // Also check if chat input is disabled (sometimes Gemini disables input when rate limited)
    try {
      const inputSelector = "div[contenteditable=\"true\"]";
      const input = await this.page.$(inputSelector);
      if (input) {
        const isDisabled = await input.evaluate((el: any) => {
          return el.disabled || el.hasAttribute("disabled");
        });

        if (isDisabled) {
          // Check if there's an error message near the input
          const parent = await input.evaluateHandle((el) => el.parentElement);
          const parentEl = parent.asElement();
          if (parentEl) {
            try {
              const parentText = await parentEl.innerText();
              const lower = parentText.toLowerCase();
              if (keywords.some((k) => lower.includes(k))) {
                log.error(`🚫 Rate limit detected: Chat input disabled with error message`);
                return true;
              }
            } catch {
              // Ignore
            }
          }
        }
      }
    } catch {
      // Ignore errors checking input state
    }

    return false;
  }

  /**
   * Reset the chat history (start a new conversation)
   */
  async reset(): Promise<void> {
    const resetOnce = async (): Promise<void> => {
      if (!this.initialized || !this.page || this.isPageClosedSafe()) {
        await this.init();
      }
      log.info(`🔄 [${this.sessionId}] Resetting chat history...`);
      // Reload the page to clear chat history
      await (this.page as Page).reload({ waitUntil: "domcontentloaded" });
      await settleDelay(2000);

      // Wait for interface to be ready again
      await this.waitForGeminiAppReady();

      // Reset message count
      this.messageCount = 0;
      this.updateActivity();

      log.success(`✅ [${this.sessionId}] Chat history reset`);
    };

    try {
      await resetOnce();
    } catch (error: any) {
      const msg = String(error?.message || error);
      if (/has been closed|Target .* closed|Browser has been closed|Context .* closed/i.test(msg)) {
        log.warning(`  ♻️  Detected closed page/context during reset. Recovering and retrying...`);
        this.initialized = false;
        if (this.page) { try { await this.page.close(); } catch {} }
        this.page = null;
        await this.init();
        await resetOnce();
        return;
      }
      log.error(`❌ [${this.sessionId}] Failed to reset: ${msg}`);
      throw error;
    }
  }

  /**
   * Close the session
   */
  async close(): Promise<void> {
    log.info(`🛑 Closing session ${this.sessionId}...`);

    if (this.page) {
      try {
        await this.page.close();
        this.page = null;
        log.success(`  ✅ Page closed`);
      } catch (error) {
        log.warning(`  ⚠️  Error closing page: ${error}`);
      }
    }

    this.initialized = false;
    log.success(`✅ Session ${this.sessionId} closed`);
  }

  /**
   * Update last activity timestamp
   */
  updateActivity(): void {
    this.lastActivity = Date.now();
  }

  /**
   * Check if session has expired (inactive for too long)
   */
  isExpired(timeoutSeconds: number): boolean {
    const inactiveSeconds = (Date.now() - this.lastActivity) / 1000;
    return inactiveSeconds > timeoutSeconds;
  }

  /**
   * Get session information
   */
  getInfo(): SessionInfo {
    const now = Date.now();
    return {
      id: this.sessionId,
      created_at: this.createdAt,
      last_activity: this.lastActivity,
      age_seconds: (now - this.createdAt) / 1000,
      inactive_seconds: (now - this.lastActivity) / 1000,
      message_count: this.messageCount,
      gemini_url: this.geminiUrl,
    };
  }

  /**
   * Get the underlying page (for advanced operations)
   */
  getPage(): Page | null {
    return this.page;
  }

  /**
   * Check if session is initialized
   */
  isInitialized(): boolean {
    return this.initialized && this.page !== null;
  }
}
