# Curriculum — 10 Code-Red Topics

**Version:** 1.0.0

---

Each topic = one slide (sometimes two if before/after needs more breathing
room). Every entry below specifies the **exact teaching point**, the
**before/after content**, and any **special components** used.

## Slide 00 — Title

- **File:** `slides/00-title.tsx`
- **Title:** "Code-Red Review Guide"
- **Subtitle:** "10 transformations that make code reviewable"
- **Body:** Centered logo + author attribution (Md. Alim Ul Karim, Riseup Asia
  LLC) + "Press → to begin"

---

## Slide 01 — Naming conventions

- **File:** `slides/01-naming-conventions.tsx`
- **Eyebrow:** "Naming"
- **Title:** "PascalCase everywhere, no underscores"
- **Teaching point:** Identifiers, DB columns, JSON keys, types — all
  PascalCase. Acronyms stay fully uppercase (`UrlParser`, not `URLParser`).
- **Before:**
  ```ts
  const user_id = 1;
  const URL_parser = ...;
  type http_response = ...;
  ```
- **After:**
  ```ts
  const UserId = 1;
  const URLParser = ...;
  type HTTPResponse = ...;
  ```

---

## Slide 02 — Nested if-else → zero nesting

- **File:** `slides/02-nested-if-else.tsx`
- **Eyebrow:** "Code Red"
- **Title:** "Pyramid logic → guard clauses"
- **Teaching point:** Never nest `if` statements. Each precondition gets its
  own positively-named guard returning early.
- **Before:** 4-level pyramid (see example in `02-slide-authoring.md`)
- **After:** Flat guards using `isValidOrder`, `hasActiveUser`, `hasItems`
- **Component:** `<CodeDiff layout="stacked" morphOnReveal />`

---

## Slide 03 — Boolean prefixes (Is / Has / Can)

- **File:** `slides/03-boolean-prefixes.tsx`
- **Eyebrow:** "Naming"
- **Title:** "Booleans tell the truth"
- **Teaching point:** Boolean variables must start with `Is`, `Has`, `Can`,
  `Should`. Functions returning bool get the same prefix.
- **Before:**
  ```ts
  const active = true;
  const items = order.items.length > 0;
  function valid(x) { return x != null; }
  ```
- **After:**
  ```ts
  const IsActive = true;
  const HasItems = order.items.length > 0;
  function IsValid(x) { return x != null; }
  ```

---

## Slide 04 — AppError wrapper

- **File:** `slides/04-app-error-wrapper.tsx`
- **Eyebrow:** "Errors"
- **Title:** "Wrap every error with file:line context"
- **Teaching point:** Raw `throw err` loses context. Use `AppError.wrap(err,
  "PaymentService.Charge")` so logs always show where the failure originated.
- **Before:**
  ```ts
  try { await charge(order); }
  catch (err) { throw err; }
  ```
- **After:**
  ```ts
  try { await charge(order); }
  catch (err) {
    throw AppError.wrap(err, 'PaymentService.Charge', { OrderId });
  }
  ```
- **Body addition:** Show the resulting log line side-by-side: raw stack vs.
  structured `{ Code, File, Line, Message, Cause }`.

---

## Slide 05 — Structured logging

- **File:** `slides/05-structured-logging.tsx`
- **Eyebrow:** "Errors"
- **Title:** "One line per event, fully structured"
- **Teaching point:** Logs must be machine-readable JSON (or key=value),
  include the calling file/path, never use `console.log` in production code.
- **Before:**
  ```ts
  console.log('failed to charge ' + orderId + ': ' + err.message);
  ```
- **After:**
  ```ts
  logger.error('PaymentService.ChargeFailed', {
    File: __filename, OrderId, Cause: err.message,
  });
  ```

---

## Slide 06 — Magic strings → enums / constants

- **File:** `slides/06-magic-strings.tsx`
- **Eyebrow:** "Code Red"
- **Title:** "Magic strings are bugs in disguise"
- **Teaching point:** Never compare a string literal in two places. Promote to
  an enum or `const` so the compiler catches typos.
- **Before:**
  ```ts
  if (order.status === 'shipped') { ... }
  if (order.status === 'shippped') { ... } // typo, silent bug
  ```
- **After:**
  ```ts
  enum OrderStatus { Pending, Shipped, Delivered }
  if (order.Status === OrderStatus.Shipped) { ... }
  ```

---

## Slide 07 — Function & file metrics

- **File:** `slides/07-function-and-file-metrics.tsx`
- **Eyebrow:** "Code Red"
- **Title:** "Small files, small functions"
- **Teaching point:** Functions 8–15 lines. Files < 300 lines. React components
  < 100 lines. If it doesn't fit, decompose.
- **Visual:** Two stacked bars showing a 73-line monster function vs. four
  small extracted functions of 12, 9, 11, 8 lines.

---

## Slide 08 — Two-operand max in conditions

- **File:** `slides/08-two-operand-max.tsx`
- **Eyebrow:** "Code Red"
- **Title:** "Max 2 operands per condition"
- **Teaching point:** `if (a && b && c && d)` is unreadable — extract a named
  helper.
- **Before:**
  ```ts
  if (user.IsActive && order.HasItems && payment.IsAuthorized && !order.IsLocked) { ... }
  ```
- **After:**
  ```ts
  if (CanShipOrder(user, order, payment)) { ... }

  function CanShipOrder(user, order, payment) {
    if (!user.IsActive) return false;
    if (!order.HasItems) return false;
    if (!payment.IsAuthorized) return false;
    return !order.IsLocked;
  }
  ```

---

## Slide 09 — Positively named guards

- **File:** `slides/09-positively-named-guards.tsx`
- **Eyebrow:** "Naming"
- **Title:** "Negate the variable, not the function"
- **Teaching point:** `if (!isInvalid(x))` is double-negation. Always name the
  guard for the *positive* condition.
- **Before:**
  ```ts
  if (!isInvalid(input) && !isMissing(token)) { ... }
  ```
- **After:**
  ```ts
  if (IsValid(input) && IsPresent(token)) { ... }
  ```

---

## Slide 10 — Spec-first workflow

- **File:** `slides/10-spec-first-workflow.tsx`
- **Eyebrow:** "Process"
- **Title:** "Spec → Issue → Code"
- **Teaching point:** No code change without a spec entry or issue. Show the
  flow as a 3-step diagram.
- **Visual:** Horizontal arrow diagram: `spec/<area>/NN-name.md` → `03-issues/`
  → PR. Each box pulses sequentially.

---

## Slide 11 — Cache invalidation

- **File:** `slides/11-cache-invalidation.tsx`
- **Eyebrow:** "Architecture"
- **Title:** "Caches must invalidate on mutation"
- **Teaching point:** Every cache has an explicit TTL AND an invalidation hook
  on the related mutation. Deterministic keys, no hidden state.
- **Before:**
  ```ts
  const cache = new Map();
  function GetUser(id) {
    if (cache.has(id)) return cache.get(id);
    const u = db.fetch(id);
    cache.set(id, u);
    return u;
  }
  // UpdateUser never clears the cache → stale reads forever
  ```
- **After:**
  ```ts
  const cache = new TTLCache({ ttl: 60_000 });
  function GetUser(id) { return cache.get(id) ?? cache.set(id, db.fetch(id)); }
  function UpdateUser(id, patch) {
    db.update(id, patch);
    cache.delete(id);            // ← invalidate
  }
  ```

---

## Slide 12 — Closing

- **File:** `slides/12-closing.tsx`
- **Title:** "Apply one transformation per PR"
- **Body:** Recap of the 10 transformations as a checklist. Footer with
  `coding-guidelines-v15` repo link.

## Topic-to-GIF mapping

The Remotion pipeline (see [07-gif-generation.md](./07-gif-generation.md)) emits
one `.gif` per topic for embedding on the main landing page:

| GIF file | Source slide |
|----------|--------------|
| `nested-if.gif` | Slide 02 |
| `naming.gif` | Slide 01 |
| `boolean-prefixes.gif` | Slide 03 |
| `app-error.gif` | Slide 04 |
| `logging.gif` | Slide 05 |
| `magic-strings.gif` | Slide 06 |
| `metrics.gif` | Slide 07 |
| `two-operand.gif` | Slide 08 |
| `positive-guards.gif` | Slide 09 |
| `cache-invalidation.gif` | Slide 11 |

## Cross-references

- Slide authoring: [02-slide-authoring.md](./02-slide-authoring.md)
- GIF generation: [07-gif-generation.md](./07-gif-generation.md)
