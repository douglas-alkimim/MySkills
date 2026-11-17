import type { Page } from "patchright";

export async function sleep(ms: number): Promise<void> {
  if (!Number.isFinite(ms) || ms < 0) throw new Error("Delay must be a non-negative finite number");
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function settleDelay(ms: number): Promise<void> {
  await sleep(ms);
}

export async function fillDeterministically(
  page: Page,
  selector: string,
  text: string,
): Promise<void> {
  const input = page.locator(selector).first();
  await input.waitFor({ state: "visible" });
  await input.fill(text);
}
