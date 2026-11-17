import { randomBytes } from "node:crypto";

interface ReceiptRecord {
  operation: string;
  resources: string[];
  stateHash: string;
  expiresAt: number;
}

export class ConfirmationReceiptError extends Error {
  constructor(
    public readonly code: "RECEIPT_UNKNOWN" | "RECEIPT_EXPIRED" | "RECEIPT_SCOPE_MISMATCH",
    message: string,
  ) {
    super(message);
    this.name = "ConfirmationReceiptError";
  }
}

export class ConfirmationReceiptStore {
  private readonly receipts = new Map<string, ReceiptRecord>();

  issue(operation: string, resources: string[], stateHash: string, ttlMs = 5 * 60_000): { receipt: string; expiresAt: string } {
    const receipt = randomBytes(32).toString("base64url");
    const expiresAt = Date.now() + ttlMs;
    this.receipts.set(receipt, {
      operation,
      resources: [...resources].sort(),
      stateHash,
      expiresAt,
    });
    return { receipt, expiresAt: new Date(expiresAt).toISOString() };
  }

  consume(receipt: string, operation: string, resources: string[], stateHash: string): void {
    const record = this.receipts.get(receipt);
    if (!record) throw new ConfirmationReceiptError("RECEIPT_UNKNOWN", "Confirmation receipt is unknown or already used");
    this.receipts.delete(receipt);
    if (Date.now() > record.expiresAt) {
      throw new ConfirmationReceiptError("RECEIPT_EXPIRED", "Confirmation receipt has expired");
    }
    const expectedResources = JSON.stringify([...resources].sort());
    if (record.operation !== operation || JSON.stringify(record.resources) !== expectedResources || record.stateHash !== stateHash) {
      throw new ConfirmationReceiptError("RECEIPT_SCOPE_MISMATCH", "Confirmed operation, resources, or resource state changed");
    }
  }
}

export const confirmationReceipts = new ConfirmationReceiptStore();
