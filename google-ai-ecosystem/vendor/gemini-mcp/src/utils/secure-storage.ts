import { execFile } from "node:child_process";
import { randomBytes } from "node:crypto";
import { chmod, mkdir, rename, rm, stat, writeFile } from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

export class SecureStorageError extends Error {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "SecureStorageError";
  }
}

export class SecureStorage {
  async atomicWrite(filePath: string, data: string | Uint8Array): Promise<void> {
    const directory = path.dirname(filePath);
    await mkdir(directory, { recursive: true, mode: 0o700 });
    const suffix = randomBytes(8).toString("hex");
    const temporaryPath = path.join(directory, `.${path.basename(filePath)}.${suffix}.tmp`);
    const backupPath = path.join(directory, `.${path.basename(filePath)}.${suffix}.bak`);

    try {
      await writeFile(temporaryPath, data, { mode: 0o600, flag: "wx" });
      await this.hardenFile(temporaryPath);

      if (process.platform === "win32") {
        let hadExisting = false;
        try {
          await rename(filePath, backupPath);
          hadExisting = true;
        } catch (error) {
          if (!isMissing(error)) throw error;
        }
        try {
          await rename(temporaryPath, filePath);
          if (hadExisting) await rm(backupPath, { force: true });
        } catch (error) {
          if (hadExisting) await rename(backupPath, filePath).catch(() => undefined);
          throw error;
        }
      } else {
        await rename(temporaryPath, filePath);
      }
    } catch (error) {
      await rm(temporaryPath, { force: true }).catch(() => undefined);
      throw new SecureStorageError(`Secure write failed for ${path.basename(filePath)}`, {
        cause: error,
      });
    }
  }

  async verify(filePath: string): Promise<void> {
    if (process.platform === "win32") {
      await this.verifyWindowsAcl(filePath);
      return;
    }
    const mode = (await stat(filePath)).mode & 0o777;
    if ((mode & 0o077) !== 0) {
      throw new SecureStorageError(`Insecure POSIX mode ${mode.toString(8)} on ${path.basename(filePath)}`);
    }
  }

  private async hardenFile(filePath: string): Promise<void> {
    if (process.platform === "win32") {
      const principal = process.env.USERNAME;
      if (!principal) throw new SecureStorageError("USERNAME is unavailable for Windows ACL hardening");
      await execFileAsync("icacls.exe", [filePath, "/inheritance:r", "/grant:r", `${principal}:(R,W)`], {
        windowsHide: true,
      });
      await this.verifyWindowsAcl(filePath);
      return;
    }
    await chmod(filePath, 0o600);
    await this.verify(filePath);
  }

  private async verifyWindowsAcl(filePath: string): Promise<void> {
    const principal = process.env.USERNAME;
    if (!principal) throw new SecureStorageError("USERNAME is unavailable for Windows ACL verification");
    const { stdout } = await execFileAsync("icacls.exe", [filePath], { windowsHide: true });
    const normalized = stdout.toLowerCase();
    if (!normalized.includes(principal.toLowerCase()) || normalized.includes("everyone:") || normalized.includes("users:")) {
      throw new SecureStorageError(`Windows ACL verification failed for ${path.basename(filePath)}`);
    }
  }
}

function isMissing(error: unknown): boolean {
  return typeof error === "object" && error !== null && "code" in error && error.code === "ENOENT";
}

export const secureStorage = new SecureStorage();
