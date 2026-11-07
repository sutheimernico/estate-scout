import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { Sheet } from "./Sheet";

function setup(onClose = vi.fn()) {
  render(
    <Sheet title="Test" onClose={onClose}>
      <input aria-label="eins" />
      <button type="button">zwei</button>
    </Sheet>,
  );
  return onClose;
}

describe("Sheet", () => {
  it("closes on Escape", () => {
    const onClose = setup();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("keeps Tab inside the dialog in both directions", () => {
    setup();
    const close = screen.getByRole("button", { name: "Schließen" });
    const last = screen.getByRole("button", { name: "zwei" });
    last.focus();
    fireEvent.keyDown(document, { key: "Tab" });
    expect(document.activeElement).toBe(close);
    fireEvent.keyDown(document, { key: "Tab", shiftKey: true });
    expect(document.activeElement).toBe(last);
  });

  it("gives focus back to the opener on close", () => {
    const opener = document.createElement("button");
    document.body.append(opener);
    opener.focus();
    const { unmount } = render(<Sheet title="T" onClose={() => {}}>x</Sheet>);
    unmount();
    expect(document.activeElement).toBe(opener);
    opener.remove();
  });
});
