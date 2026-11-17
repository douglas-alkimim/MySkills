/**
 * Custom Error Types for Gemini App MCP Server
 */

/**
 * Error thrown when Gemini App rate limit is exceeded
 *
 * The service message is observational. No fixed limit, reset time, plan
 * multiplier or account-switch workaround is inferred by the MCP.
 */
export class RateLimitError extends Error {
  constructor(message: string = "Gemini reported that the current request cannot continue because of a quota or capacity limit") {
    super(message);
    this.name = "RateLimitError";

    // Maintain proper stack trace for where error was thrown (V8 only)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, RateLimitError);
    }
  }
}

/**
 * Error thrown when authentication fails
 *
 * This error can suggest cleanup workflow for persistent issues.
 * Especially useful when upgrading from an older installation.
 */
export class AuthenticationError extends Error {
  suggestCleanup: boolean;

  constructor(message: string, suggestCleanup: boolean = false) {
    super(message);
    this.name = "AuthenticationError";
    this.suggestCleanup = suggestCleanup;

    // Maintain proper stack trace for where error was thrown (V8 only)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, AuthenticationError);
    }
  }
}

/**
 * Error returned to MCP clients when a visible, user-driven login is required.
 */
export class AuthenticationRequiredError extends AuthenticationError {
  readonly code = "AUTH_REQUIRED";

  constructor(
    message: string = "Gemini authentication is missing or expired. Run setup_auth with show_browser=true, complete login, close the browser if it remains open, then retry the original tool call."
  ) {
    super(message);
    this.name = "AuthenticationRequiredError";

    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, AuthenticationRequiredError);
    }
  }
}
