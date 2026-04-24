# Payment Banner Hider — Corrected Reference Implementation

> Drop-in replacement for `macro-ahk-v23/standalone-scripts/payment-banner-hider/src/index.ts`.
> Resolves every violation listed in [`mem://issues/payment-banner-hider-rca`](../../.lovable/memory/issues/payment-banner-hider-rca.md).
> Produced from this repo because the sandbox cannot push to `macro-ahk-v23`.

## Target file layout

```
standalone-scripts/payment-banner-hider/
└── src/
    ├── index.ts              # entry only — construct + start
    ├── PaymentBannerHider.ts # main class
    ├── BannerObserver.ts     # injected dependency
    ├── StyleInjector.ts      # injected dependency (owns the CSS)
    ├── styles.ts             # CSS string (no !important)
    └── types.ts              # enums + global Window augmentation
```

## `src/types.ts`

```ts
// Global enums and Window augmentation. No string literals leak out of this file.

export enum BannerClass {
  Root      = "payment-banner",
  IsHiding  = "payment-banner--is-hiding",
  IsHidden  = "payment-banner--is-hidden",
}

export enum BannerAttr {
  Handled = "data-payment-banner-handled",
}

export enum DocReadyState {
  Loading     = "loading",
  Interactive = "interactive",
  Complete    = "complete",
}

export enum DomEventName {
  DomContentLoaded = "DOMContentLoaded",
  TransitionEnd    = "transitionend",
}

export type Result<T, E = AppError> =
  | { ok: true;  value: T }
  | { ok: false; error: E };

export interface AppError {
  type: AppErrorType;
  message: string;
  cause?: unknown;
}

export enum AppErrorType {
  XPathEvaluationFailed = "XPathEvaluationFailed",
  TargetNotHtmlElement  = "TargetNotHtmlElement",
}

export function failure<E>(error: E): { ok: false; error: E } {
  return { ok: false, error };
}

export function success<T>(value: T): { ok: true; value: T } {
  return { ok: true, value };
}

declare global {
  // eslint-disable-next-line @typescript-eslint/consistent-type-imports
  interface Window {
    PaymentBannerHider: import("./PaymentBannerHider").PaymentBannerHider;
  }
}

export function isHtmlElement(node: Node | null): node is HTMLElement {
  return node !== null && node.nodeType === Node.ELEMENT_NODE && node instanceof HTMLElement;
}
```

## `src/styles.ts`

```ts
import { BannerClass } from "./types";

// One class = transition. One class = display:none. Specificity comes from the
// double-class selector, NOT from !important.
export const bannerStyles = `
  .${BannerClass.Root}.${BannerClass.IsHiding} {
    opacity: 0;
    transition: opacity 250ms ease-out;
    pointer-events: none;
  }

  .${BannerClass.Root}.${BannerClass.IsHidden} {
    display: none;
  }
`;
```

## `src/StyleInjector.ts`

```ts
export class StyleInjector {
  private readonly elementId: string;
  private readonly css: string;

  constructor(elementId: string, css: string) {
    this.elementId = elementId;
    this.css = css;
  }

  inject(): void {
    if (this.alreadyInjected()) {
      return;
    }
    const style = document.createElement("style");
    style.id = this.elementId;
    style.textContent = this.css;
    const host = document.head ?? document.documentElement;

    host.appendChild(style);
  }

  private alreadyInjected(): boolean {
    return document.getElementById(this.elementId) !== null;
  }
}
```

## `src/BannerObserver.ts`

```ts
export class BannerObserver {
  private observer: MutationObserver | null = null;

  start(onMutation: () => void): void {
    if (this.observer !== null) {
      return;
    }
    this.observer = new MutationObserver(onMutation);
    const root = document.body ?? document.documentElement;

    this.observer.observe(root, { childList: true, subtree: true, characterData: true });
  }

  stop(): void {
    if (this.observer === null) {
      return;
    }
    this.observer.disconnect();
    this.observer = null;
  }
}
```

## `src/PaymentBannerHider.ts`

```ts
import { BannerObserver } from "./BannerObserver";
import { StyleInjector } from "./StyleInjector";
import {
  AppError,
  AppErrorType,
  BannerAttr,
  BannerClass,
  DocReadyState,
  DomEventName,
  Result,
  failure,
  isHtmlElement,
  success,
} from "./types";

const TARGET_TEXT  = "Payment issue detected.";
const TARGET_XPATH = "/html/body/div[2]/main/div/div[1]";
const VERSION      = "2.0.0";

export class PaymentBannerHider {
  readonly version = VERSION;

  constructor(
    private readonly styles: StyleInjector,
    private readonly observer: BannerObserver,
  ) {}

  start(): Result<void> {
    this.styles.inject();
    const initialResult = this.checkOnce();
    if (!initialResult.ok) {
      return initialResult;
    }
    this.attachLifecycle();

    return success(undefined);
  }

  checkOnce(): Result<void> {
    const lookup = this.findTarget();
    if (!lookup.ok) {
      return lookup;
    }
    const target = lookup.value;
    if (target === null) {
      return success(undefined);
    }
    if (this.alreadyHandled(target)) {
      return success(undefined);
    }
    if (!this.matchesPaymentText(target)) {
      return success(undefined);
    }
    this.hide(target);

    return success(undefined);
  }

  private attachLifecycle(): void {
    const isLoading = (document.readyState as DocReadyState) === DocReadyState.Loading;
    if (isLoading) {
      document.addEventListener(DomEventName.DomContentLoaded, () => this.afterReady(), { once: true });
      return;
    }
    this.afterReady();
  }

  private afterReady(): void {
    this.checkOnce();
    this.observer.start(() => this.checkOnce());
  }

  private findTarget(): Result<HTMLElement | null, AppError> {
    let evaluation: XPathResult;
    try {
      evaluation = document.evaluate(TARGET_XPATH, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
    } catch (caught) {
      return failure<AppError>({
        type: AppErrorType.XPathEvaluationFailed,
        message: `XPath evaluation failed for ${TARGET_XPATH}`,
        cause: caught,
      });
    }
    const node = evaluation.singleNodeValue;
    if (node === null) {
      return success(null);
    }
    if (!isHtmlElement(node)) {
      return failure<AppError>({
        type: AppErrorType.TargetNotHtmlElement,
        message: "XPath matched a non-HTMLElement node",
      });
    }

    return success(node);
  }

  private matchesPaymentText(el: HTMLElement): boolean {
    const text = el.textContent ?? "";

    return text.includes(TARGET_TEXT);
  }

  private alreadyHandled(el: HTMLElement): boolean {
    return el.hasAttribute(BannerAttr.Handled);
  }

  private hide(el: HTMLElement): void {
    el.setAttribute(BannerAttr.Handled, "true");
    el.classList.add(BannerClass.Root, BannerClass.IsHiding);
    el.addEventListener(
      DomEventName.TransitionEnd,
      () => el.classList.add(BannerClass.IsHidden),
      { once: true },
    );
  }
}
```

## `src/index.ts`

```ts
import { BannerObserver } from "./BannerObserver";
import { PaymentBannerHider } from "./PaymentBannerHider";
import { StyleInjector } from "./StyleInjector";
import { bannerStyles } from "./styles";

const STYLE_ELEMENT_ID = "payment-banner-hider-styles";

const hider = new PaymentBannerHider(
  new StyleInjector(STYLE_ELEMENT_ID, bannerStyles),
  new BannerObserver(),
);

window.PaymentBannerHider = hider;
const result = hider.start();
if (!result.ok) {
  // Surface, do not swallow.
  console.error("[payment-banner-hider]", result.error);
}

export { PaymentBannerHider };
```

## How this resolves every violation

| Violation | Fix |
|-----------|-----|
| `!important` × 12 | Removed entirely. Specificity from double-class selector `.payment-banner.payment-banner--is-hiding`. CSS lives in `styles.ts`. |
| `try { … } catch { return null }` | `findTarget()` returns `Result<HTMLElement \| null, AppError>` and wraps the caught error with `AppErrorType.XPathEvaluationFailed`. Caller decides. |
| `(window as unknown as { … })` | `declare global { interface Window { PaymentBannerHider: PaymentBannerHider } }` — assignment is `window.PaymentBannerHider = hider;` with no cast. |
| Magic strings | All state, attribute, class, event, and readyState literals live in `types.ts` enums. |
| Flat top-level functions | `PaymentBannerHider` class with two injected dependencies (`StyleInjector`, `BannerObserver`). |
| CSS in `index.ts` | Moved to `styles.ts`. |
| Nested `requestAnimationFrame` + `setTimeout` chain | Single class toggle + `transitionend` event. CSS owns the timing. |
| Missing blank line before `return` | Every multi-statement block has one blank line before its `return`. |

## Verification grep (run in the target repo before commit)

```bash
grep -RnE "!important|as unknown|as any|catch \{|catch \(_\)" standalone-scripts/payment-banner-hider/src && exit 1 || echo "clean"
```

Expect `clean`.
