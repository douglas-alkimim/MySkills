import { createHash } from "node:crypto";
import { lstat, readlink, readdir, realpath, rm } from "node:fs/promises";
import path from "node:path";
import { CONFIG } from "../config.js";
import { confirmationReceipts } from "./confirmation-receipts.js";

export interface CleanupRoots {
  dataDir: string;
  browserStateDir: string;
  chromeProfileDir: string;
  chromeInstancesDir: string;
  libraryPath: string;
}

export interface CleanupPreview {
  operation: "cleanup_gemini_mcp_data";
  categories: Array<{ name: string; description: string; paths: string[]; totalBytes: number; optional: false }>;
  paths: string[];
  totalSizeBytes: number;
  scopeHash: string;
  receipt: string;
  expiresAt: string;
}

export interface CleanupResult {
  success: boolean;
  removedPaths: string[];
  retainedPaths: string[];
  changedPaths: string[];
  failedPaths: Array<{ path: string; error: string }>;
  totalSizeBytes: number;
}

interface Snapshot {
  resources: string[];
  entries: string[];
  totalSizeBytes: number;
  scopeHash: string;
}

const OPERATION = "cleanup_gemini_mcp_data";

export class CleanupManager {
  constructor(private readonly roots: CleanupRoots = defaultRoots()) {}

  async preview(preserveLibrary = true): Promise<CleanupPreview> {
    const snapshot = await this.snapshot(preserveLibrary);
    const issued = confirmationReceipts.issue(OPERATION, snapshot.resources, snapshot.scopeHash);
    return {
      operation: OPERATION,
      categories: [{
        name: "gemini_mcp_owned_data",
        description: "Authentication state and MCP-owned Chrome profiles only",
        paths: snapshot.resources,
        totalBytes: snapshot.totalSizeBytes,
        optional: false,
      }],
      paths: snapshot.resources,
      totalSizeBytes: snapshot.totalSizeBytes,
      scopeHash: snapshot.scopeHash,
      receipt: issued.receipt,
      expiresAt: issued.expiresAt,
    };
  }

  async execute(receipt: string, preserveLibrary = true): Promise<CleanupResult> {
    const snapshot = await this.snapshot(preserveLibrary);
    confirmationReceipts.consume(receipt, OPERATION, snapshot.resources, snapshot.scopeHash);

    const removedPaths: string[] = [];
    const retainedPaths: string[] = [];
    const failedPaths: Array<{ path: string; error: string }> = [];
    for (const target of snapshot.resources) {
      try {
        await this.assertOwnedTarget(target);
        await rm(target, { recursive: true, force: true });
        removedPaths.push(target);
      } catch (error) {
        retainedPaths.push(target);
        failedPaths.push({
          path: target,
          error: error instanceof Error ? error.message : "cleanup failed",
        });
      }
    }
    return {
      success: failedPaths.length === 0,
      removedPaths,
      retainedPaths,
      changedPaths: [],
      failedPaths,
      totalSizeBytes: snapshot.totalSizeBytes,
    };
  }

  private async snapshot(preserveLibrary: boolean): Promise<Snapshot> {
    const candidates = [
      this.roots.browserStateDir,
      this.roots.chromeProfileDir,
      this.roots.chromeInstancesDir,
      ...(!preserveLibrary ? [this.roots.libraryPath] : []),
    ];
    const resources: string[] = [];
    const entries: string[] = [];
    let totalSizeBytes = 0;
    for (const candidate of candidates) {
      try {
        const canonical = await this.assertOwnedTarget(candidate);
        resources.push(canonical);
        const tree = await this.snapshotTree(canonical);
        entries.push(...tree.entries);
        totalSizeBytes += tree.totalSizeBytes;
      } catch (error) {
        if (isMissing(error)) continue;
        throw error;
      }
    }
    resources.sort();
    entries.sort();
    const scopeHash = createHash("sha256")
      .update(JSON.stringify({ resources, entries, preserveLibrary }))
      .digest("hex");
    return { resources, entries, totalSizeBytes, scopeHash };
  }

  private async assertOwnedTarget(candidate: string): Promise<string> {
    const [canonicalRoot, canonicalTarget] = await Promise.all([
      realpath(this.roots.dataDir),
      realpath(candidate),
    ]);
    const relative = path.relative(canonicalRoot, canonicalTarget);
    if (relative === "" || relative === ".." || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) {
      throw new Error("Cleanup target is outside the Gemini MCP data root");
    }
    return canonicalTarget;
  }

  private async snapshotTree(root: string): Promise<{ entries: string[]; totalSizeBytes: number }> {
    const entries: string[] = [];
    let totalSizeBytes = 0;
    const visit = async (current: string): Promise<void> => {
      const info = await lstat(current);
      const relative = path.relative(root, current) || ".";
      if (info.isSymbolicLink()) {
        const target = await realpath(current);
        const ownedRoot = await realpath(this.roots.dataDir);
        const boundary = path.relative(ownedRoot, target);
        if (boundary === ".." || boundary.startsWith(`..${path.sep}`) || path.isAbsolute(boundary)) {
          throw new Error(`Cleanup tree contains an external link at ${relative}`);
        }
        entries.push(`${relative}|link|${await readlink(current)}|${info.mtimeMs}`);
        return;
      }
      entries.push(`${relative}|${info.isDirectory() ? "dir" : "file"}|${info.size}|${info.mtimeMs}`);
      if (info.isDirectory()) {
        for (const name of (await readdir(current)).sort()) await visit(path.join(current, name));
      } else {
        totalSizeBytes += info.size;
      }
    };
    await visit(root);
    return { entries, totalSizeBytes };
  }
}

function defaultRoots(): CleanupRoots {
  return {
    dataDir: CONFIG.dataDir,
    browserStateDir: CONFIG.browserStateDir,
    chromeProfileDir: CONFIG.chromeProfileDir,
    chromeInstancesDir: CONFIG.chromeInstancesDir,
    libraryPath: path.join(CONFIG.dataDir, "library.json"),
  };
}

function isMissing(error: unknown): boolean {
  return typeof error === "object" && error !== null && "code" in error && error.code === "ENOENT";
}
