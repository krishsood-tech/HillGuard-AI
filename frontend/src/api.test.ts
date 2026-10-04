import { describe, expect, it } from "vitest";
import { CATEGORY_META, timeAgo } from "./api";

describe("helpers", () => {
  it("has distinct hazard categories", () => {
    expect(Object.keys(CATEGORY_META).length).toBeGreaterThanOrEqual(7);
  });
  it("formats recent times", () => {
    expect(timeAgo(new Date().toISOString())).toMatch(/now|minute/i);
  });
});
