/**
 * MCP Tool Handlers
 *
 * Implements the logic for all MCP tools.
 */

import { SessionManager } from "../session/session-manager.js";
import { AuthManager } from "../auth/auth-manager.js";
import { ConversationLibrary } from "../library/conversation-library.js";
import type { AddConversationInput, UpdateConversationInput } from "../library/types.js";
import { CONFIG, applyBrowserOptions, type BrowserOptions } from "../config.js";
import { log } from "../utils/logger.js";
import type {
  AskQuestionResult,
  ToolResult,
  ProgressCallback,
} from "../types.js";
import { AuthenticationRequiredError, RateLimitError } from "../errors.js";
import { CleanupManager } from "../utils/cleanup-manager.js";
import { settleDelay } from "../utils/interaction-utils.js";
import fs from "fs/promises";
import path from "path";
import type { Locator, Page } from "patchright";
import type { BrowserSession } from "../session/browser-session.js";
import { createHash } from "node:crypto";
import { confirmationReceipts } from "../utils/confirmation-receipts.js";

const FOLLOW_UP_REMINDER =
  "\n\nEXTREMELY IMPORTANT: Is that ALL you need to know? You can always ask another question using the same session ID! Think about it carefully: before you reply to the user, review their original request and this answer. If anything is still unclear or missing, ask me another question first.";

type GeminiSpecialTool = "deep_research" | "create_video" | "create_image";
type MediaKind = "video" | "image";
type AttachmentPurpose = "reference" | "style" | "character" | "composition";

interface MediaAttachment {
  path: string;
  purpose: AttachmentPurpose;
  description?: string;
}

interface ValidatedMediaAttachment extends MediaAttachment {
  absolutePath: string;
  fileName: string;
}

interface MediaCandidate {
  src: string;
  ready: boolean;
  inResponse: boolean;
}

export function isMediaCapacityMessage(value: string): boolean {
  return /(?:unusually high traffic|full capacity|please try again later|capacidade (?:máxima|esgotada)|muito tráfego|tente novamente mais tarde)/i.test(
    value
  );
}

export function isMediaTimeoutMessage(value: string): boolean {
  return /^MEDIA_TIMEOUT:/i.test(value);
}

/**
 * MCP Tool Handlers
 */
export class ToolHandlers {
  private sessionManager: SessionManager;
  private authManager: AuthManager;
  private library: ConversationLibrary;

  constructor(sessionManager: SessionManager, authManager: AuthManager, library: ConversationLibrary) {
    this.sessionManager = sessionManager;
    this.authManager = authManager;
    this.library = library;
  }

  private async authenticationFailure(error: unknown): Promise<ToolResult<never> | null> {
    const message = error instanceof Error ? error.message : String(error);
    const isAuthenticationFailure =
      error instanceof AuthenticationRequiredError ||
      /AUTH_REQUIRED|failed to authenticate|fresh login required|authentication.*(?:missing|expired|invalid)/i.test(message);
    if (!isAuthenticationFailure) {
      return null;
    }

    return {
      success: false,
      code: "AUTH_REQUIRED",
      auth_status: await this.authManager.getAuthStatus(),
      error: message,
      recommended_action:
        "Call setup_auth with show_browser=true. Let the user finish Google login in the visible Chrome window, close it if needed, then retry the original tool call. Normal calls remain headless.",
    };
  }

  /**
   * Handle ask_question tool
   */
  async handleAskQuestion(
    args: {
      question: string;
      session_id?: string;
      conversation_id?: string;
      gemini_url?: string;
      show_browser?: boolean;
      browser_options?: BrowserOptions;
    },
    sendProgress?: ProgressCallback
  ): Promise<ToolResult<AskQuestionResult>> {
    const { question, session_id, conversation_id, gemini_url, show_browser, browser_options } = args;

    log.info(`🔧 [TOOL] ask_question called`);
    log.info(`  Question: "${question.substring(0, 100)}"...`);
    if (session_id) {
      log.info(`  Session ID: ${session_id}`);
    }
    if (conversation_id) {
      log.info(`  Conversation ID: ${conversation_id}`);
    }
    if (gemini_url) {
      log.info(`  Conversation URL: ${gemini_url}`);
    }

    try {
      // Resolve conversation URL
      let resolvedConversationUrl = gemini_url;

      if (!resolvedConversationUrl && conversation_id) {
        const conversation = this.library.incrementUseCount(conversation_id);
        if (!conversation) {
          throw new Error(`Conversation not found in library: ${conversation_id}`);
        }

        resolvedConversationUrl = conversation.url;
        log.info(`  Resolved conversation: ${conversation.name}`);
      } else if (!resolvedConversationUrl) {
        const active = this.library.getActiveConversation();
        if (active) {
          const conversation = this.library.incrementUseCount(active.id);
          if (!conversation) {
            throw new Error(`Active conversation not found: ${active.id}`);
          }
          resolvedConversationUrl = conversation.url;
          log.info(`  Using active conversation: ${conversation.name}`);
        }
      }

      // Progress: Getting or creating session
      await sendProgress?.("Getting or creating browser session...", 1, 5);

      // Apply browser options temporarily
      const originalConfig = { ...CONFIG };
      const effectiveConfig = applyBrowserOptions(browser_options, show_browser);
      Object.assign(CONFIG, effectiveConfig);

      // Calculate overrideHeadless parameter for session manager
      // show_browser takes precedence over browser_options.headless
      let overrideHeadless: boolean | undefined = undefined;
      if (show_browser !== undefined) {
        overrideHeadless = show_browser;
      } else if (browser_options?.show !== undefined) {
        overrideHeadless = browser_options.show;
      } else if (browser_options?.headless !== undefined) {
        overrideHeadless = !browser_options.headless;
      }

      try {
        // Get or create session (with headless override to handle mode changes)
        const session = await this.sessionManager.getOrCreateSession(
          session_id,
          resolvedConversationUrl,
          overrideHeadless
        );

      // Progress: Asking question
      await sendProgress?.("Asking question to Gemini App...", 2, 5);

      // Ask the question (pass progress callback)
      const rawAnswer = await session.ask(question, sendProgress);
      const answer = `${rawAnswer.trimEnd()}${FOLLOW_UP_REMINDER}`;

      // Get session info
      const sessionInfo = session.getInfo();

      const result: AskQuestionResult = {
        status: "success",
        question,
        answer,
        session_id: session.sessionId,
        gemini_url: session.geminiUrl,
        session_info: {
          age_seconds: sessionInfo.age_seconds,
          message_count: sessionInfo.message_count,
          last_activity: sessionInfo.last_activity,
        },
      };

        // Progress: Complete
        await sendProgress?.("Question answered successfully!", 5, 5);

        log.success(`✅ [TOOL] ask_question completed successfully`);
        return {
          success: true,
          data: result,
        };
      } finally {
        // Restore original CONFIG
        Object.assign(CONFIG, originalConfig);
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);

      const authenticationFailure = await this.authenticationFailure(error);
      if (authenticationFailure) {
        log.warning(`🔑 [TOOL] ask_question requires interactive authentication`);
        return authenticationFailure;
      }

      // Special handling for rate limit errors
      if (error instanceof RateLimitError || errorMessage.toLowerCase().includes("rate limit")) {
        log.error(`🚫 [TOOL] Rate limit detected`);
        return {
          success: false,
          code: "QUOTA_OR_CAPACITY_OBSERVED",
          error: "Gemini reported a quota or capacity condition for the current account. Retry only when the service indicates it is appropriate.",
          observed_service_message: errorMessage,
          retryable: true,
        };
      }

      log.error(`❌ [TOOL] ask_question failed: ${errorMessage}`);
      return {
        success: false,
        error: errorMessage,
      };
    }
  }

  /**
   * Handle list_sessions tool
   */
  async handleListSessions(): Promise<
    ToolResult<{
      active_sessions: number;
      max_sessions: number;
      session_timeout: number;
      oldest_session_seconds: number;
      total_messages: number;
      sessions: Array<{
        id: string;
        created_at: number;
        last_activity: number;
        age_seconds: number;
        inactive_seconds: number;
        message_count: number;
        gemini_url: string;
      }>;
    }> 
  > {
    log.info(`🔧 [TOOL] list_sessions called`);

    try {
      const stats = this.sessionManager.getStats();
      const sessions = this.sessionManager.getAllSessionsInfo();

      const result = {
        active_sessions: stats.active_sessions,
        max_sessions: stats.max_sessions,
        session_timeout: stats.session_timeout,
        oldest_session_seconds: stats.oldest_session_seconds,
        total_messages: stats.total_messages,
        sessions: sessions.map((info) => ({
          id: info.id,
          created_at: info.created_at,
          last_activity: info.last_activity,
          age_seconds: info.age_seconds,
          inactive_seconds: info.inactive_seconds,
          message_count: info.message_count,
          gemini_url: info.gemini_url,
        })),
      };

      log.success(
        `✅ [TOOL] list_sessions completed (${result.active_sessions} sessions)`
      );
      return {
        success: true,
        data: result,
      };
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      log.error(`❌ [TOOL] list_sessions failed: ${errorMessage}`);
      return {
        success: false,
        error: errorMessage,
      };
    }
  }

  /**
   * Handle close_session tool
   */
  async handleCloseSession(args: { session_id: string }): Promise<
    ToolResult<{ status: string; message: string; session_id: string }>
  > {
    const { session_id } = args;

    log.info(`🔧 [TOOL] close_session called`);
    log.info(`  Session ID: ${session_id}`);

    try {
      const closed = await this.sessionManager.closeSession(session_id);

      if (closed) {
        log.success(`✅ [TOOL] close_session completed`);
        return {
          success: true,
          data: {
            status: "success",
            message: `Session ${session_id} closed successfully`,
            session_id,
          },
        };
      } else {
        log.warning(`⚠️  [TOOL] Session ${session_id} not found`);
        return {
          success: false,
          error: `Session ${session_id} not found`,
        };
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      log.error(`❌ [TOOL] close_session failed: ${errorMessage}`);
      return {
        success: false,
        error: errorMessage,
      };
    }
  }

  /**
   * Handle reset_session tool
   */
  async handleResetSession(args: { session_id: string }): Promise<
    ToolResult<{ status: string; message: string; session_id: string }>
  > {
    const { session_id } = args;

    log.info(`🔧 [TOOL] reset_session called`);
    log.info(`  Session ID: ${session_id}`);

    try {
      const session = this.sessionManager.getSession(session_id);

      if (!session) {
        log.warning(`⚠️  [TOOL] Session ${session_id} not found`);
        return {
          success: false,
          error: `Session ${session_id} not found`,
        };
      }

      await session.reset();

      log.success(`✅ [TOOL] reset_session completed`);
      return {
        success: true,
        data: {
          status: "success",
          message: `Session ${session_id} reset successfully`,
          session_id,
        },
      };
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      log.error(`❌ [TOOL] reset_session failed: ${errorMessage}`);
      return {
        success: false,
        error: errorMessage,
      };
    }
  }

  /**
   * Handle get_health tool
   */
  async handleGetHealth(): Promise<
    ToolResult<{
      status: string;
      authenticated: boolean;
      auth_status: "unconfigured" | "valid" | "repairable" | "expired" | "switch_requested" | "failed_recoverable";
      browser_visible: boolean;
      recommended_action?: string;
      gemini_url: string;
      active_sessions: number;
      max_sessions: number;
      session_timeout: number;
      total_messages: number;
      headless: boolean;
      locale: string;
      timezone_id: string;
      troubleshooting_tip?: string;
    }> 
  > {
    log.info(`🔧 [TOOL] get_health called`);

    try {
      // Check authentication status
      const authStatus = await this.authManager.getAuthStatus();
      const authenticated = authStatus === "valid";
      const browser = this.sessionManager.getBrowserVisibility();

      // Get session stats
      const stats = this.sessionManager.getStats();

      const result = {
        status: "ok",
        authenticated,
        auth_status: authStatus,
        browser_visible: browser.visible,
        gemini_url: CONFIG.geminiUrl || "not configured",
        active_sessions: stats.active_sessions,
        max_sessions: stats.max_sessions,
        session_timeout: stats.session_timeout,
        total_messages: stats.total_messages,
        headless: browser.active ? !browser.visible : CONFIG.headless,
        locale: CONFIG.locale,
        timezone_id: CONFIG.timezoneId,
        // Add troubleshooting tip if not authenticated
        ...((!authenticated) && {
          troubleshooting_tip:
            "Authentication needs user action. Run setup_auth(show_browser=true), finish Google login, close the browser if needed, then retry.",
          recommended_action:
            "Call setup_auth with show_browser=true, let the user log in, then retry the original headless tool call."
        }),
      };

      log.success(`✅ [TOOL] get_health completed`);
      return {
        success: true,
        data: result,
      };
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      log.error(`❌ [TOOL] get_health failed: ${errorMessage}`);
      return {
        success: false,
        error: errorMessage,
      };
    }
  }

  /**
   * Handle setup_auth tool
   *
   * Opens a browser window for manual login with live progress updates.
   * The operation waits synchronously for login completion (up to 10 minutes).
   */
  async handleSetupAuth(
    args: {
      show_browser?: boolean;
      browser_options?: BrowserOptions;
    },
    sendProgress?: ProgressCallback
  ): Promise<
    ToolResult<{
      status: string;
      message: string;
      authenticated: boolean;
      duration_seconds?: number;
    }> 
  > {
    const { show_browser, browser_options } = args;

    // CRITICAL: Send immediate progress to reset timeout from the very start
    await sendProgress?.("Initializing authentication setup...", 0, 10);

    log.info(`🔧 [TOOL] setup_auth called`);
    if (show_browser !== undefined) {
      log.info(`  Show browser: ${show_browser}`);
    }

    const startTime = Date.now();

    // Apply browser options temporarily
    const originalConfig = { ...CONFIG };
    const effectiveConfig = applyBrowserOptions(browser_options, show_browser);
    Object.assign(CONFIG, effectiveConfig);

    try {
      // Progress: Starting
      await sendProgress?.("Preparing authentication browser...", 1, 10);

      log.info(`  🌐 Opening browser for interactive login...`);

      // Progress: Opening browser
      await sendProgress?.("Opening browser window...", 2, 10);

      // Perform setup with progress updates (uses CONFIG internally)
      const success = await this.authManager.performSetup(sendProgress);

      const durationSeconds = (Date.now() - startTime) / 1000;

      if (success) {
        // Progress: Complete
        await sendProgress?.("Authentication saved successfully!", 10, 10);

        log.success(`✅ [TOOL] setup_auth completed (${durationSeconds.toFixed(1)}s)`);
        return {
          success: true,
          data: {
            status: "authenticated",
            message: "Successfully authenticated and saved browser state",
            authenticated: true,
            duration_seconds: durationSeconds,
          },
        };
      } else {
        log.error(`❌ [TOOL] setup_auth failed (${durationSeconds.toFixed(1)}s)`);
        return {
          success: false,
          code: "AUTH_INCOMPLETE",
          auth_status: await this.authManager.getAuthStatus(),
          error: "Authentication failed or was cancelled",
          recommended_action:
            "Run setup_auth with show_browser=true again and keep the window open until Gemini finishes loading.",
        };
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      const durationSeconds = (Date.now() - startTime) / 1000;
      log.error(`❌ [TOOL] setup_auth failed: ${errorMessage} (${durationSeconds.toFixed(1)}s)`);
      return {
        success: false,
        error: errorMessage,
      };
    } finally {
      // Restore original CONFIG
      Object.assign(CONFIG, originalConfig);
    }
  }

  /**
   * Handle re_auth tool
   *
   * Performs a complete re-authentication:
   * 1. Closes all active browser sessions
   * 2. Deletes all saved authentication data (cookies, Chrome profile)
   * 3. Opens browser for fresh Google login
   *
   * Repair is non-destructive. Account switching is separate and confirmed.
   */
  async handleReAuth(
    args: {
      mode?: "repair" | "switch_account";
      receipt?: string;
      show_browser?: boolean;
      browser_options?: BrowserOptions;
    },
    sendProgress?: ProgressCallback
  ): Promise<
    ToolResult<{
      status: string;
      message: string;
      authenticated: boolean;
      duration_seconds?: number;
      receipt?: string;
      expires_at?: string;
      resources?: string[];
      state_version?: string;
    }> 
  > {
    const { mode = "repair", receipt, show_browser, browser_options } = args;

    await sendProgress?.("Preparing re-authentication...", 0, 12);
    log.info(`🔧 [TOOL] re_auth called`);
    if (show_browser !== undefined) {
      log.info(`  Show browser: ${show_browser}`);
    }

    const startTime = Date.now();

    if (mode === "switch_account" && !receipt) {
      const preview = await this.authManager.previewAccountSwitch();
      return {
        success: true,
        data: {
          status: "switch_preview",
          message: "Review the exact MCP-owned authentication resources and confirm before switching accounts.",
          authenticated: false,
          receipt: preview.receipt,
          expires_at: preview.expiresAt,
          resources: preview.resources,
          state_version: preview.stateVersion,
        },
      };
    }

    // Apply browser options temporarily
    const originalConfig = { ...CONFIG };
    const effectiveConfig = applyBrowserOptions(browser_options, show_browser);
    Object.assign(CONFIG, effectiveConfig);

    try {
      // Close active MCP sessions before opening a visible recovery browser.
      await sendProgress?.("Closing all active sessions...", 1, 12);
      log.info("  🛑 Closing all sessions...");
      await this.sessionManager.closeAllSessions();
      log.success("  ✅ All sessions closed");

      const success = mode === "switch_account"
        ? await this.authManager.performAccountSwitch(receipt!, sendProgress, show_browser)
        : await this.authManager.performSetup(sendProgress, show_browser);

      const durationSeconds = (Date.now() - startTime) / 1000;

      if (success) {
        await sendProgress?.("Re-authentication complete!", 12, 12);
        log.success(`✅ [TOOL] re_auth completed (${durationSeconds.toFixed(1)}s)`);
        return {
          success: true,
          data: {
            status: "authenticated",
            message: mode === "switch_account"
              ? "Account switch completed after explicit scope confirmation."
              : "Authentication repair completed without pre-emptive profile deletion.",
            authenticated: true,
            duration_seconds: durationSeconds,
          },
        };
      } else {
        log.error(`❌ [TOOL] re_auth failed (${durationSeconds.toFixed(1)}s)`);
        return {
          success: false,
          error: "Re-authentication failed or was cancelled",
        };
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      const durationSeconds = (Date.now() - startTime) / 1000;
      log.error(
        `❌ [TOOL] re_auth failed: ${errorMessage} (${durationSeconds.toFixed(1)}s)`
      );
      return {
        success: false,
        error: errorMessage,
      };
    } finally {
      // Restore original CONFIG
      Object.assign(CONFIG, originalConfig);
    }
  }

  /**
   * Handle add_conversation tool
   */
  async handleAddConversation(args: AddConversationInput): Promise<ToolResult<{ conversation: any }>> {
    log.info(`🔧 [TOOL] add_conversation called`);
    log.info(`  Name: ${args.name}`);

    try {
      const conversation = this.library.addConversation(args);
      log.success(`✅ [TOOL] add_conversation completed: ${conversation.id}`);
      return {
        success: true,
        data: { conversation },
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      log.error(`❌ [TOOL] add_conversation failed: ${errorMessage}`);
      return {
        success: false,
        error: errorMessage,
      };
    }
  }

  /**
   * Handle list_conversations tool
   */
  async handleListConversations(): Promise<ToolResult<{ conversations: any[] }>> {
    log.info(`🔧 [TOOL] list_conversations called`);

    try {
      const conversations = this.library.listConversations();
      log.success(`✅ [TOOL] list_conversations completed (${conversations.length} conversations)`);
      return {
        success: true,
        data: { conversations },
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      log.error(`❌ [TOOL] list_conversations failed: ${errorMessage}`);
      return {
        success: false,
        error: errorMessage,
      };
    }
  }

  /**
   * Handle get_conversation tool
   */
  async handleGetConversation(args: { id: string }): Promise<ToolResult<{ conversation: any }>> {
    log.info(`🔧 [TOOL] get_conversation called`);
    log.info(`  ID: ${args.id}`);

    try {
      const conversation = this.library.getConversation(args.id);
      if (!conversation) {
        log.warning(`⚠️  [TOOL] Conversation not found: ${args.id}`);
        return {
          success: false,
          error: `Conversation not found: ${args.id}`,
        };
      }

      log.success(`✅ [TOOL] get_conversation completed: ${conversation.name}`);
      return {
        success: true,
        data: { conversation },
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      log.error(`❌ [TOOL] get_conversation failed: ${errorMessage}`);
      return {
        success: false,
        error: errorMessage,
      };
    }
  }

  /**
   * Handle select_conversation tool
   */
  async handleSelectConversation(args: { id: string }): Promise<ToolResult<{ conversation: any }>> {
    log.info(`🔧 [TOOL] select_conversation called`);
    log.info(`  ID: ${args.id}`);

    try {
      const conversation = this.library.selectConversation(args.id);
      log.success(`✅ [TOOL] select_conversation completed: ${conversation.name}`);
      return {
        success: true,
        data: { conversation },
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      log.error(`❌ [TOOL] select_conversation failed: ${errorMessage}`);
      return {
        success: false,
        error: errorMessage,
      };
    }
  }

  /**
   * Handle update_conversation tool
   */
  async handleUpdateConversation(args: UpdateConversationInput): Promise<ToolResult<{ conversation: any }>> {
    log.info(`🔧 [TOOL] update_conversation called`);
    log.info(`  ID: ${args.id}`);

    try {
      const conversation = this.library.updateConversation(args);
      log.success(`✅ [TOOL] update_conversation completed: ${conversation.name}`);
      return {
        success: true,
        data: { conversation },
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      log.error(`❌ [TOOL] update_conversation failed: ${errorMessage}`);
      return {
        success: false,
        error: errorMessage,
      };
    }
  }

  /**
   * Handle remove_conversation tool
   */
  async handleRemoveConversation(args: { id: string; receipt?: string }): Promise<ToolResult<{
    status: "preview" | "removed";
    removed: boolean;
    closed_sessions: number;
    conversation?: { id: string; name: string };
    receipt?: string;
    expires_at?: string;
  }>> {
    log.info(`🔧 [TOOL] remove_conversation called`);
    log.info(`  ID: ${args.id}`);

    try {
      const conversation = this.library.getConversation(args.id);
      if (!conversation) {
        log.warning(`⚠️  [TOOL] Conversation not found: ${args.id}`);
        return {
          success: false,
          error: `Conversation not found: ${args.id}`,
        };
      }

      const resource = `conversation:${conversation.id}`;
      const stateHash = createHash("sha256").update(JSON.stringify(conversation)).digest("hex");
      if (!args.receipt) {
        const issued = confirmationReceipts.issue("remove_conversation", [resource], stateHash);
        return {
          success: true,
          data: {
            status: "preview",
            removed: false,
            closed_sessions: 0,
            conversation: { id: conversation.id, name: conversation.name },
            receipt: issued.receipt,
            expires_at: issued.expiresAt,
          },
        };
      }
      confirmationReceipts.consume(args.receipt, "remove_conversation", [resource], stateHash);

      const removed = this.library.removeConversation(args.id);
      if (removed) {
        const closedSessions = await this.sessionManager.closeSessionsForConversation(
          conversation.url
        );
        log.success(`✅ [TOOL] remove_conversation completed`);
        return {
          success: true,
          data: { status: "removed", removed: true, closed_sessions: closedSessions },
        };
      } else {
        log.warning(`⚠️  [TOOL] Conversation not found: ${args.id}`);
        return {
          success: false,
          error: `Conversation not found: ${args.id}`,
        };
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      log.error(`❌ [TOOL] remove_conversation failed: ${errorMessage}`);
      return {
        success: false,
        error: errorMessage,
      };
    }
  }

  /**
   * Handle search_conversations tool
   */
  async handleSearchConversations(args: { query: string }): Promise<ToolResult<{ conversations: any[] }>> {
    log.info(`🔧 [TOOL] search_conversations called`);
    log.info(`  Query: "${args.query}"`);

    try {
      const conversations = this.library.searchConversations(args.query);
      log.success(`✅ [TOOL] search_conversations completed (${conversations.length} results)`);
      return {
        success: true,
        data: { conversations },
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      log.error(`❌ [TOOL] search_conversations failed: ${errorMessage}`);
      return {
        success: false,
        error: errorMessage,
      };
    }
  }

  /**
   * Handle get_library_stats tool
   */
  async handleGetLibraryStats(): Promise<ToolResult<any>> {
    log.info(`🔧 [TOOL] get_library_stats called`);

    try {
      const stats = this.library.getStats();
      log.success(`✅ [TOOL] get_library_stats completed`);
      return {
        success: true,
        data: stats,
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      log.error(`❌ [TOOL] get_library_stats failed: ${errorMessage}`);
      return {
        success: false,
        error: errorMessage,
      };
    }
  }

  /**
   * Handle cleanup_data tool
   *
   * ULTRATHINK Deep Cleanup - scans entire system for ALL Gemini App MCP files
   */
  async handleCleanupData(
    args: { receipt?: string; preserve_library?: boolean }
  ): Promise<
    ToolResult<{
      status: string;
      preview?: {
        categories: Array<{ name: string; description: string; paths: string[]; totalBytes: number; optional: boolean }>;
        totalPaths: number;
        totalSizeBytes: number;
        scopeHash: string;
        receipt: string;
        expiresAt: string;
      };
      result?: {
        removedPaths: string[];
        retainedPaths: string[];
        changedPaths: string[];
        failedPaths: Array<{ path: string; error: string }>;
        totalSizeBytes: number;
      };
    }> 
  > {
    const { receipt, preserve_library = true } = args;

    log.info(`🔧 [TOOL] cleanup_data called`);
    log.info(`  Preserve Library: ${preserve_library}`);

    const cleanupManager = new CleanupManager();

    try {
      if (!receipt) {
        log.info("  📋 Generating MCP-owned cleanup preview...");
        const preview = await cleanupManager.preview(preserve_library);
        log.info(`  Found ${preview.paths.length} managed roots`);

        return {
          success: true,
          data: {
            status: "preview",
            preview: {
              categories: preview.categories,
              totalPaths: preview.paths.length,
              totalSizeBytes: preview.totalSizeBytes,
              scopeHash: preview.scopeHash,
              receipt: preview.receipt,
              expiresAt: preview.expiresAt,
            },
          },
        };
      } else {
        log.info("  🗑️  Executing the exact confirmed MCP-owned cleanup scope...");
        const result = await cleanupManager.execute(receipt, preserve_library);

        if (result.success) {
          log.success(`✅ [TOOL] cleanup_data completed - removed ${result.removedPaths.length} roots`);
        } else {
          log.warning(`⚠️  [TOOL] cleanup_data completed with ${result.failedPaths.length} errors`);
        }

        return {
          success: result.success,
          data: {
            status: result.success ? "completed" : "partial",
            result: {
              removedPaths: result.removedPaths,
              retainedPaths: result.retainedPaths,
              changedPaths: result.changedPaths,
              failedPaths: result.failedPaths,
              totalSizeBytes: result.totalSizeBytes,
            },
          },
        };
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      log.error(`❌ [TOOL] cleanup_data failed: ${errorMessage}`);
      return {
        success: false,
        error: errorMessage,
      };
    }
  }

  private getSessionPage(session: BrowserSession): Page {
    const page = session.getPage();
    if (!page) {
      throw new Error("Session page not initialized");
    }
    return page;
  }

  private async clickFirstVisible(
    page: Page,
    selectors: string[]
  ): Promise<string | null> {
    for (const selector of selectors) {
      try {
        const matches = page.locator(selector);
        const count = await matches.count();
        for (let index = 0; index < count; index++) {
          const candidate = matches.nth(index);
          if (await candidate.isVisible()) {
            await candidate.click();
            return selector;
          }
        }
      } catch {
        continue;
      }
    }
    return null;
  }

  private async visibleControlSummary(page: Page): Promise<string> {
    try {
      const controls = await page.locator(
        "button, [role='menuitem'], [role='option'], [role='radio'], mat-option, li"
      )
        .evaluateAll((elements) =>
          elements
            .filter((element) => {
              const rect = element.getBoundingClientRect();
              return rect.width > 0 && rect.height > 0;
            })
            .slice(0, 120)
            .map((element) => ({
              tag: element.tagName.toLowerCase(),
              role: element.getAttribute("role") || "",
              className: (element.getAttribute("class") || "").slice(0, 120),
              text: (element.textContent || "").trim().replace(/\s+/g, " ").slice(0, 80),
              aria: element.getAttribute("aria-label") || "",
            }))
        );
      return JSON.stringify(controls);
    } catch {
      return "[]";
    }
  }

  private async pageSummary(page: Page): Promise<string> {
    try {
      return JSON.stringify(
        await page.evaluate(() => {
          const browserGlobal: any = globalThis as any;
          const document: any = browserGlobal.document;
          const normalize = (value: string | null | undefined) =>
            (value || "").trim().replace(/\s+/g, " ");
          const fields = Array.from(
            document.querySelectorAll("input, textarea, [contenteditable='true'], [role='textbox']")
          ).map((element: any) => ({
            tag: element.tagName.toLowerCase(),
            aria: element.getAttribute("aria-label") || "",
            placeholder: element.getAttribute("placeholder") || "",
            className: normalize(element.getAttribute("class")).slice(0, 160),
            visible: element.getBoundingClientRect().width > 0 && element.getBoundingClientRect().height > 0,
          }));
          return {
            url: browserGlobal.location.href,
            title: document.title,
            bodyTail: normalize(document.body?.innerText).slice(-2000),
            fields,
          };
        })
      ).slice(0, 12_000);
    } catch (error) {
      return JSON.stringify({ error: String(error) });
    }
  }

  private async tryFindPromptInput(page: Page): Promise<Locator | null> {
    const selectors = [
      '[contenteditable="true"][aria-label*="comando" i]',
      '[contenteditable="true"][aria-label*="prompt" i]',
      'div[role="textbox"][contenteditable="true"]',
      'div[contenteditable="true"]',
      "textarea",
    ];

    for (const selector of selectors) {
      const candidates = page.locator(selector);
      const count = await candidates.count();
      for (let index = 0; index < count; index++) {
        const candidate = candidates.nth(index);
        if (await candidate.isVisible()) {
          return candidate;
        }
      }
    }

    return null;
  }

  private async findPromptInput(page: Page): Promise<Locator> {
    const input = await this.tryFindPromptInput(page);
    if (input) {
      return input;
    }

    throw new Error(
      `Could not find Gemini prompt input. Page: ${await this.pageSummary(page)}. ` +
      `Visible controls: ${await this.visibleControlSummary(page)}`
    );
  }

  private async collectMediaCandidates(
    page: Page,
    kind: MediaKind
  ): Promise<MediaCandidate[]> {
    const selector = kind === "video" ? "video" : "img";
    return page.locator(selector).evaluateAll((elements, mediaKind) =>
      elements
        .map((element) => {
          const rect = element.getBoundingClientRect();
          const media = element as any;
          const isVideo = mediaKind === "video";
          const src = isVideo
            ? media.currentSrc || media.src
            : media.currentSrc || media.src;
          const ready = isVideo
            ? media.readyState >= 2
            : media.complete &&
              media.naturalWidth >= 256 &&
              media.naturalHeight >= 256;
          const inResponse = Boolean(
            element.closest(
              ".to-user-container, [data-message-author='assistant'], " +
              "[data-message-role='assistant'], [data-author='assistant'], " +
              "[class*='response'], [class*='generated']"
            )
          );
          return {
            src,
            ready,
            inResponse,
            visible: rect.width >= 200 && rect.height >= 150,
          };
        })
        .filter((candidate) => candidate.src && candidate.visible)
        .map(({ src, ready, inResponse }) => ({ src, ready, inResponse })),
      kind
    );
  }

  private async waitForGeneratedMedia(
    page: Page,
    kind: MediaKind,
    baselineSources: Set<string>,
    baselineBodyText: string,
    sendProgress?: ProgressCallback
  ): Promise<MediaCandidate[]> {
    const deadline = Date.now() + CONFIG.mediaGenerationTimeoutMs;
    let lastProgressAt = 0;

    while (Date.now() < deadline) {
      const candidates = (await this.collectMediaCandidates(page, kind))
        .filter((candidate) => !baselineSources.has(candidate.src) && candidate.ready)
        .sort((left, right) => Number(right.inResponse) - Number(left.inResponse));

      if (candidates.length > 0) {
        return kind === "video" ? candidates.slice(0, 1) : candidates.slice(0, 4);
      }

      const alerts = await page.locator("[role='alert']").allInnerTexts().catch(() => []);
      const failure = alerts.find((text) =>
        /não foi possível gerar|falha ao gerar|could not generate|something went wrong/i.test(text)
      );
      if (failure) {
        throw new Error(`Gemini media generation failed: ${failure}`);
      }

      const currentTitle = await page.title().catch(() => "");
      const currentBodyText = await page.locator("body").innerText().catch(() => "");
      const newBodyText = currentBodyText.startsWith(baselineBodyText)
        ? currentBodyText.slice(baselineBodyText.length)
        : currentBodyText.slice(-8_000);
      if (isMediaCapacityMessage(`${currentTitle}\n${newBodyText}`)) {
        throw new Error(
          `MEDIA_CAPACITY: Gemini ${kind} generation is temporarily at capacity. Please retry later.`
        );
      }

      const responseTexts = await page
        .locator("model-response message-content, model-response .model-response-text")
        .allInnerTexts()
        .catch(() => []);
      const refusal = responseTexts.find((text) =>
        /não tenho acesso a esse conteúdo|normalmente posso ajudar|não fui programado|can't (?:help|access)|unable to (?:help|access)/i.test(text)
      );
      if (refusal) {
        throw new Error(`Gemini media generation was refused: ${refusal.trim()}`);
      }

      if (Date.now() - lastProgressAt >= 30_000) {
        lastProgressAt = Date.now();
        const elapsedSeconds = Math.round(
          (CONFIG.mediaGenerationTimeoutMs - (deadline - Date.now())) / 1000
        );
        await sendProgress?.(
          `Waiting for Gemini ${kind} generation (${elapsedSeconds}s elapsed)...`,
          4,
          5
        );
      }

      await page.waitForTimeout(3_000);
    }

    throw new Error(
      `MEDIA_TIMEOUT: Gemini did not expose a ready generated ${kind} within ` +
      `${Math.round(CONFIG.mediaGenerationTimeoutMs / 1000)} seconds.`
    );
  }

  private extensionForContentType(contentType: string, kind: MediaKind): string {
    const normalized = contentType.toLowerCase();
    if (normalized.includes("webm")) return "webm";
    if (normalized.includes("webp")) return "webp";
    if (normalized.includes("jpeg")) return "jpg";
    if (normalized.includes("png")) return "png";
    if (normalized.includes("gif")) return "gif";
    if (normalized.includes("mp4")) return "mp4";
    return kind === "video" ? "mp4" : "png";
  }

  private async saveMediaSource(
    page: Page,
    source: string,
    kind: MediaKind,
    index: number
  ): Promise<string> {
    let bytes: Buffer;
    let contentType = kind === "video" ? "video/mp4" : "image/png";

    if (source.startsWith("data:")) {
      const match = source.match(/^data:([^;,]+)?(;base64)?,(.*)$/s);
      if (!match) throw new Error("Unsupported generated media data URL");
      contentType = match[1] || contentType;
      bytes = match[2]
        ? Buffer.from(match[3], "base64")
        : Buffer.from(decodeURIComponent(match[3]), "utf8");
    } else if (source.startsWith("blob:")) {
      const base64 = await page.evaluate(async (url) => {
        const response = await fetch(url);
        const blob = await response.blob();
        const buffer = new Uint8Array(await blob.arrayBuffer());
        let binary = "";
        const chunkSize = 0x8000;
        for (let offset = 0; offset < buffer.length; offset += chunkSize) {
          binary += String.fromCharCode(...buffer.subarray(offset, offset + chunkSize));
        }
        return {
          data: globalThis.btoa(binary),
          type: blob.type,
        };
      }, source);
      contentType = base64.type || contentType;
      bytes = Buffer.from(base64.data, "base64");
    } else {
      const response = await page.context().request.get(source);
      if (!response.ok()) {
        throw new Error(`Generated media download failed with HTTP ${response.status()}`);
      }
      contentType = response.headers()["content-type"] || contentType;
      bytes = await response.body();
    }

    if (bytes.length === 0) {
      throw new Error("Generated media download returned an empty file");
    }

    await fs.mkdir(CONFIG.outputDir, { recursive: true });
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    const extension = this.extensionForContentType(contentType, kind);
    const outputPath = path.join(
      CONFIG.outputDir,
      `gemini-${kind}-${timestamp}-${index + 1}.${extension}`
    );
    await fs.writeFile(outputPath, bytes);
    return outputPath;
  }

  private async validateMediaAttachments(
    attachments: MediaAttachment[] | undefined
  ): Promise<ValidatedMediaAttachment[]> {
    if (!attachments || attachments.length === 0) {
      return [];
    }
    if (attachments.length > 8) {
      throw new Error("At most 8 media attachments are supported per request");
    }

    const allowedPurposes = new Set<AttachmentPurpose>([
      "reference",
      "style",
      "character",
      "composition",
    ]);
    const allowedExtensions = new Set([".png", ".jpg", ".jpeg", ".webp", ".gif"]);
    const validated: ValidatedMediaAttachment[] = [];

    for (const attachment of attachments) {
      if (!attachment || typeof attachment.path !== "string" || attachment.path.trim() === "") {
        throw new Error("Every attachment must include a non-empty path");
      }
      if (!allowedPurposes.has(attachment.purpose)) {
        throw new Error(`Invalid attachment purpose: ${String(attachment.purpose)}`);
      }

      const absolutePath = path.resolve(attachment.path);
      const extension = path.extname(absolutePath).toLowerCase();
      if (!allowedExtensions.has(extension)) {
        throw new Error(
          `Unsupported attachment type for ${absolutePath}. Use PNG, JPEG, WebP, or GIF.`
        );
      }

      const stats = await fs.stat(absolutePath).catch(() => null);
      if (!stats?.isFile()) {
        throw new Error(`Attachment is not a readable file: ${absolutePath}`);
      }
      if (stats.size > 25 * 1024 * 1024) {
        throw new Error(`Attachment exceeds the 25 MB limit: ${absolutePath}`);
      }

      validated.push({
        ...attachment,
        absolutePath,
        fileName: path.basename(absolutePath),
      });
    }
    return validated;
  }

  private buildMediaPrompt(
    kind: MediaKind,
    userPrompt: string,
    attachments: ValidatedMediaAttachment[]
  ): string {
    const attachmentLines = attachments.length > 0
      ? attachments.map((attachment, index) =>
          `${index + 1}. ${attachment.fileName} — purpose: ${attachment.purpose}` +
          (attachment.description ? ` — instruction: ${attachment.description}` : "")
        ).join("\n")
      : "No reference images were supplied.";

    return [
      `MASTER INSTRUCTIONS — GEMINI ${kind.toUpperCase()} GENERATION`,
      `Create the requested ${kind} as the final deliverable. Follow the user's creative intent precisely.`,
      "Treat every uploaded image only according to its declared purpose. Preserve requested identity and composition cues without inventing claims about real people.",
      "Do not answer with a tutorial or prompt rewrite. Generate the media now. If a minor detail is unspecified, make a coherent visual choice and continue.",
      "",
      "USER REQUEST",
      userPrompt.trim(),
      "",
      "UPLOADED REFERENCES",
      attachmentLines,
      "",
      "OUTPUT CONTRACT",
      `Return the generated ${kind} in Gemini's media result so the MCP can download it.`,
    ].join("\n");
  }

  private async uploadMediaAttachments(
    page: Page,
    attachments: ValidatedMediaAttachment[],
    sendProgress?: ProgressCallback
  ): Promise<void> {
    if (attachments.length === 0) {
      return;
    }

    await sendProgress?.(`Uploading ${attachments.length} reference image(s)...`, 3, 6);
    const filePaths = attachments.map((attachment) => attachment.absolutePath);
    const directInputs = page.locator('input[type="file"]');
    if (await directInputs.count() > 0) {
      await directInputs.first().setInputFiles(filePaths);
      await page.waitForTimeout(1_000);
      return;
    }

    const toolsButton = await this.clickFirstVisible(page, [
      'button[aria-label="Envio e ferramentas"]',
      'button[aria-label*="ferrament" i]',
      'button[aria-label*="tools" i]',
      'button:has-text("Tools")',
    ]);
    if (!toolsButton) {
      throw new Error(
        `Could not open Gemini's upload controls. Visible controls: ${await this.visibleControlSummary(page)}`
      );
    }

    await page.waitForTimeout(500);
    const chooserPromise = page.waitForEvent("filechooser", { timeout: 10_000 });
    const uploadClicked = await this.clickFirstVisible(page, [
      '[role="menuitem"]:has-text("Enviar arquivos")',
      '[role="menuitem"]:has-text("Upload files")',
      'button:has-text("Enviar arquivos")',
      'button:has-text("Upload files")',
      '[aria-label*="upload" i]',
      '[aria-label*="enviar arquivo" i]',
    ]);
    if (!uploadClicked) {
      void chooserPromise.catch(() => undefined);
      throw new Error(
        `Could not find Gemini's file upload action. Visible controls: ${await this.visibleControlSummary(page)}`
      );
    }
    const chooser = await chooserPromise;
    await chooser.setFiles(filePaths);
    await page.waitForTimeout(1_000);
  }

  private async runMediaGeneration(
    page: Page,
    tool: "create_video" | "create_image",
    prompt: string,
    attachments: ValidatedMediaAttachment[],
    sendProgress?: ProgressCallback
  ): Promise<{ result: string; files: string[]; attachmentsUsed: string[] }> {
    const kind: MediaKind = tool === "create_video" ? "video" : "image";
    const baseline = new Set(
      (await this.collectMediaCandidates(page, kind)).map((candidate) => candidate.src)
    );
    const baselineBodyText = await page.locator("body").innerText().catch(() => "");
    const input = await this.findPromptInput(page);

    await this.uploadMediaAttachments(page, attachments, sendProgress);
    const effectivePrompt = this.buildMediaPrompt(kind, prompt, attachments);

    await sendProgress?.(`Submitting ${kind} prompt to Gemini...`, 3, 5);
    await input.fill(effectivePrompt);
    await settleDelay(250);
    await input.press("Enter");

    const generated = await this.waitForGeneratedMedia(
      page,
      kind,
      baseline,
      baselineBodyText,
      sendProgress
    );
    const files: string[] = [];
    for (let index = 0; index < generated.length; index++) {
      files.push(await this.saveMediaSource(page, generated[index].src, kind, index));
    }

    return {
      result: `Gemini generated ${files.length} ${kind} file(s).`,
      files,
      attachmentsUsed: attachments.map((attachment) => attachment.absolutePath),
    };
  }

  private async prepareSpecialTool(
    page: Page,
    tool: GeminiSpecialTool
  ): Promise<string> {
    if (tool === "create_video" || tool === "create_image") {
      const isVideo = tool === "create_video";
      const targetUrl = isVideo
        ? "https://gemini.google.com/videos"
        : "https://gemini.google.com/images";
      const existingInput = await this.tryFindPromptInput(page);
      if (!existingInput) {
        await page.goto(targetUrl, {
          waitUntil: "domcontentloaded",
          timeout: Math.max(CONFIG.browserTimeout, 60_000),
        });
        await settleDelay(2_000);
      }
      await this.findPromptInput(page);
      return isVideo ? "Create videos" : "Create images";
    }

    const toolsButton = await this.clickFirstVisible(page, [
      'button[aria-label="Envio e ferramentas"]',
      'button[aria-label*="ferrament" i]',
      'button[aria-label*="tools" i]',
      'button:has-text("Tools")',
      'div[role="button"]:has-text("Tools")',
    ]);
    if (!toolsButton) {
      throw new Error(
        `Could not find Gemini tools button. Visible controls: ${await this.visibleControlSummary(page)}`
      );
    }

    await settleDelay(500);
    const deepResearchSelectors = [
      '[role="menuitemcheckbox"]:has-text("Pesquisa aprofundada")',
      '[role="menuitem"]:has-text("Pesquisa aprofundada")',
      '[role="option"]:has-text("Pesquisa aprofundada")',
      'button:has-text("Pesquisa aprofundada")',
      '[role="menuitemcheckbox"]:has-text("Deep research")',
      '[role="menuitem"]:has-text("Deep research")',
      '[role="option"]:has-text("Deep research")',
      'button:has-text("Deep research")',
      '[role="menuitem"]:has-text("Pesquisa detalhada")',
      'button:has-text("Pesquisa detalhada")',
    ];
    let selected = await this.clickFirstVisible(page, deepResearchSelectors);
    if (!selected) {
      const moreTools = await this.clickFirstVisible(page, [
        'button[aria-label="Mais ferramentas"]',
        'button:has-text("Mais ferramentas")',
        'button[aria-label="More tools"]',
        'button:has-text("More tools")',
      ]);
      if (moreTools) {
        await settleDelay(500);
        selected = await this.clickFirstVisible(page, deepResearchSelectors);
      }
    }
    if (!selected) {
      throw new Error(
        `Could not select Deep Research. Visible controls: ${await this.visibleControlSummary(page)}`
      );
    }
    return "Deep research";
  }

  /**
   * Handle select_model tool
   */
  async handleSelectModel(
    args: {
      model: string;
      session_id?: string;
    }
  ): Promise<ToolResult<{ status: string; model: string; session_id: string }>> {
    const { model, session_id } = args;

    log.info(`🔧 [TOOL] select_model called`);
    log.info(`  Model: ${model}`);

    try {
      const session = await this.sessionManager.getOrCreateSession(session_id);
      const page = this.getSessionPage(session);
      const legacyAliases: Record<string, string[]> = {
        fast: ["Rápido", "Fast", "Gemini 3"],
        thinking: ["Pensando", "Thinking"],
        pro: ["Pro"],
      };
      const modelAliases = legacyAliases[model];
      if (!modelAliases) {
        throw new Error(`Invalid model: ${model}. Must be one of: fast, thinking, pro`);
      }

      const selectorClicked = await this.clickFirstVisible(page, [
        'button[aria-label*="seletor de modo" i]',
        'button[aria-label*="model" i]',
        'button:has-text("Pro")',
        'button:has-text("Gemini 3")',
        'button:has-text("Thinking")',
      ]);
      if (!selectorClicked) {
        throw new Error(
          `Could not find model selector. Visible controls: ${await this.visibleControlSummary(page)}`
        );
      }

      await settleDelay(500);
      const optionSelectors = modelAliases.flatMap((alias) => [
        `gem-menu-item[role="menuitem"]:has-text("${alias}")`,
        `[role="menuitem"]:has-text("${alias}")`,
        `[role="option"]:has-text("${alias}")`,
      ]);
      let optionClicked = await this.clickFirstVisible(page, optionSelectors);

      // The current Gemini UI exposes a named mode (for example "Hydrogen")
      // and puts the old fast/thinking/pro distinction under Reasoning level.
      if (!optionClicked) {
        const reasoningSelectors = [
          'gem-menu-item[role="menuitem"]:has-text("Nível de raciocínio")',
          '[role="menuitem"]:has-text("Nível de raciocínio")',
          'gem-menu-item[role="menuitem"]:has-text("Reasoning level")',
          '[role="menuitem"]:has-text("Reasoning level")',
        ];
        let reasoningItem: Locator | null = null;
        for (const selector of reasoningSelectors) {
          const candidates = page.locator(selector);
          const count = await candidates.count();
          for (let index = 0; index < count; index++) {
            const candidate = candidates.nth(index);
            if (await candidate.isVisible()) {
              reasoningItem = candidate;
              break;
            }
          }
          if (reasoningItem) break;
        }

        if (reasoningItem) {
          const className = (await reasoningItem.getAttribute("class")) || "";
          const ariaChecked = await reasoningItem.getAttribute("aria-checked");
          const ariaSelected = await reasoningItem.getAttribute("aria-selected");
          const isActive =
            /(?:^|\s)active(?:\s|$)/i.test(className) ||
            ariaChecked === "true" ||
            ariaSelected === "true";
          const wantsReasoning = model !== "fast";
          if (isActive !== wantsReasoning) {
            await reasoningItem.click();
          }
          optionClicked = "reasoning-level-toggle";
        }
      }
      if (!optionClicked) {
        throw new Error(
          `Could not select model '${model}'. Visible controls: ${await this.visibleControlSummary(page)}`
        );
      }

      await settleDelay(750);
      log.success(`✅ [TOOL] select_model completed`);
      return {
        success: true,
        data: {
          status: "success",
          model,
          session_id: session.sessionId,
        },
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      log.error(`❌ [TOOL] select_model failed: ${errorMessage}`);
      return { success: false, error: errorMessage };
    }
  }

  /**
   * Handle use_gemini_tool tool
   */
  async handleUseGeminiTool(
    args: {
      tool: string;
      prompt: string;
      session_id?: string;
      attachments?: MediaAttachment[];
    },
    sendProgress?: ProgressCallback
  ): Promise<
    ToolResult<{
      status: string;
      tool: string;
      result: string;
      session_id: string;
      files?: string[];
      attachments_used?: string[];
    }>
  > {
    const { tool, prompt, session_id, attachments } = args;

    log.info(`🔧 [TOOL] use_gemini_tool called`);
    log.info(`  Tool: ${tool}`);
    log.info(`  Prompt: "${prompt.substring(0, 100)}"...`);

    try {
      if (!["deep_research", "create_video", "create_image"].includes(tool)) {
        throw new Error(
          `Invalid tool: ${tool}. Must be one of: deep_research, create_video, create_image`
        );
      }
      const specialTool = tool as GeminiSpecialTool;
      if (specialTool === "deep_research" && attachments && attachments.length > 0) {
        throw new Error("attachments are supported only for create_image and create_video");
      }
      const validatedAttachments = specialTool === "deep_research"
        ? []
        : await this.validateMediaAttachments(attachments);
      const targetUrl = specialTool === "create_video"
        ? "https://gemini.google.com/videos"
        : specialTool === "create_image"
          ? "https://gemini.google.com/images"
          : CONFIG.geminiUrl;

      await sendProgress?.("Getting or creating browser session...", 1, 5);
      const session = await this.sessionManager.getOrCreateSession(
        session_id,
        targetUrl,
        undefined
      );
      const page = this.getSessionPage(session);

      await sendProgress?.(`Preparing Gemini ${specialTool} mode...`, 2, 5);
      const displayName = await this.prepareSpecialTool(page, specialTool);

      let result: string;
      let files: string[] | undefined;
      let attachmentsUsed: string[] | undefined;
      if (specialTool === "create_video" || specialTool === "create_image") {
        const mediaResult = await this.runMediaGeneration(
          page,
          specialTool,
          prompt,
          validatedAttachments,
          sendProgress
        );
        result = mediaResult.result;
        files = mediaResult.files;
        attachmentsUsed = mediaResult.attachmentsUsed;
      } else {
        result = await session.ask(
          prompt,
          sendProgress,
          CONFIG.researchTimeoutMs,
          true
        );
      }

      await sendProgress?.("Gemini tool execution complete!", 5, 5);
      log.success(`✅ [TOOL] use_gemini_tool completed`);
      return {
        success: true,
        data: {
          status: "success",
          tool: displayName,
          result: result.trimEnd(),
          session_id: session.sessionId,
          ...(files && { files }),
          ...(attachmentsUsed && { attachments_used: attachmentsUsed }),
        },
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      const authenticationFailure = await this.authenticationFailure(error);
      if (authenticationFailure) {
        log.warning(`🔑 [TOOL] use_gemini_tool requires interactive authentication`);
        return authenticationFailure;
      }
      if (errorMessage.startsWith("MEDIA_CAPACITY:")) {
        log.warning(`⏳ [TOOL] Gemini media generation is temporarily at capacity`);
        return {
          success: false,
          code: "MEDIA_CAPACITY",
          error: errorMessage.replace(/^MEDIA_CAPACITY:\s*/, ""),
          retryable: true,
          recommended_action:
            "Retry the same create_image/create_video request later. Authentication is still valid; setup_auth is not needed.",
        };
      }
      if (isMediaTimeoutMessage(errorMessage)) {
        log.warning(`⏳ [TOOL] Gemini media generation exceeded the configured timeout`);
        return {
          success: false,
          code: "MEDIA_TIMEOUT",
          error: errorMessage.replace(/^MEDIA_TIMEOUT:\s*/i, ""),
          retryable: true,
          recommended_action:
            "Retry once with a larger MEDIA_GENERATION_TIMEOUT_MS only when the original request is still useful; do not switch accounts or duplicate concurrent generations.",
        };
      }
      log.error(`❌ [TOOL] use_gemini_tool failed: ${errorMessage}`);
      return { success: false, error: errorMessage };
    }
  }

  /**
   * Cleanup all resources (called on server shutdown)
   */
  async cleanup(): Promise<void> {
    log.info(`🧹 Cleaning up tool handlers...`);
    await this.sessionManager.closeAllSessions();
    log.success(`✅ Tool handlers cleanup complete`);
  }
}
