import { createHmac, randomBytes } from "node:crypto";

const SECRET_KEYS = /^(authorization|cookie|set-cookie|email|password|passwd|token|access_token|refresh_token|id_token|client_secret|login_email|login_password)$/i;
const CONTENT_KEYS = /^(prompt|question|query|response|answer|content|body|text|attachment)$/i;
const LABELED_CONTENT = /(Question|Prompt|Query|Answer|Response|Conversation URL|Email|Password)\s*:\s*(?:"[^"]*"|'[^']*'|[^\r\n]*)/gi;
const BEARER = /\b(Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+/gi;
const COOKIE = /\b(cookie|set-cookie)\s*[:=]\s*[^;\s]+(?:;\s*[^\r\n]*)?/gi;
const TOKEN = /\b(access[_-]?token|refresh[_-]?token|id[_-]?token|client[_-]?secret|password|passwd)\s*[:=]\s*[^\s,;}]+/gi;
const URL_PATTERN = /https?:\/\/[^\s"']+/gi;

export class Redactor {
  private readonly key: Buffer;

  constructor(key: Buffer = randomBytes(32)) {
    this.key = key;
  }

  redactText(value: string): string {
    return value
      .replace(LABELED_CONTENT, (_match, label: string) => `${label}: [REDACTED]`)
      .replace(BEARER, "$1 [REDACTED]")
      .replace(COOKIE, "$1=[REDACTED]")
      .replace(TOKEN, "$1=[REDACTED]")
      .replace(URL_PATTERN, (raw) => this.redactUrl(raw));
  }

  redact<T>(value: T, key = ""): T {
    if (SECRET_KEYS.test(key) || CONTENT_KEYS.test(key)) {
      return "[REDACTED]" as T;
    }
    if (typeof value === "string") {
      return this.redactText(value) as T;
    }
    if (Array.isArray(value)) {
      return value.map((entry) => this.redact(entry)) as T;
    }
    if (value && typeof value === "object") {
      const result: Record<string, unknown> = {};
      for (const [entryKey, entryValue] of Object.entries(value)) {
        result[entryKey] = this.redact(entryValue, entryKey);
      }
      return result as T;
    }
    return value;
  }

  correlationId(value: string): string {
    return createHmac("sha256", this.key).update(value).digest("hex").slice(0, 16);
  }

  private redactUrl(raw: string): string {
    try {
      const url = new URL(raw);
      if (url.username) url.username = "redacted";
      if (url.password) url.password = "redacted";
      if (url.search) url.search = "?[REDACTED]";
      if (url.hash) url.hash = "#[REDACTED]";
      return url.toString();
    } catch {
      return "[REDACTED_URL]";
    }
  }
}

export const redactor = new Redactor();
