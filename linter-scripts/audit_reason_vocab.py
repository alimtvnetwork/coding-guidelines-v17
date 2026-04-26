"""Shared `ignored-deleted` reason vocabulary for the placeholder linter.

This module is the **single source of truth** for the closed set of
provenance tags the placeholder linter attaches to ``ignored-deleted``
audit rows. Both the audit emitter inside
``check-placeholder-comments.py`` and the test suite under
``linter-scripts/tests/`` must import from this module so a tag
typo in either location is caught at import-time rather than
silently desynchronising the audit contract.

The module name is deliberately snake_case (legal Python identifier)
so it can be imported the normal way from siblings — unlike
``check-placeholder-comments.py`` which has to be loaded through the
``conftest_shim`` because of its hyphenated executable filename.

Public API
----------

``DELETED_REASON`` :
    ``dict[str, str]`` — provenance tag → human-readable reason
    template. R/C-old templates embed a ``{new_path}`` placeholder
    that :func:`resolve_deleted_reason` substitutes at render time.

``DELETED_REASON_FALLBACK`` :
    ``str`` — reason returned by :func:`resolve_deleted_reason` when
    a parser hands it a tag this module does not yet know about.
    Lets future parser changes degrade gracefully instead of
    crashing the audit emitter mid-render.

``DELETED_SOURCES`` :
    ``tuple[str, ...]`` — frozen render order for the closed source
    vocabulary. Drives argparse ``choices=`` for
    ``--only-deleted-source``, the per-source footer breakdown, and
    the column order of every test that pivots on source. The
    fallback message is intentionally *not* in this tuple — it's a
    safety net, not an operator-targetable value.

``resolve_deleted_reason(source, new_path=None)`` :
    Format the human-readable reason for one ``ignored-deleted``
    row. Tags with a ``{new_path}`` placeholder are substituted
    (missing ``new_path`` → literal ``"<unknown>"`` so the row stays
    scannable); flat tags return their template verbatim; unknown
    tags return :data:`DELETED_REASON_FALLBACK`.

Adding a new source
-------------------

1. Add the entry to :data:`DELETED_REASON` (with or without a
   ``{new_path}`` placeholder).
2. Append the tag to :data:`DELETED_SOURCES` at the position that
   matches your desired footer-breakdown render order.
3. Update the parser that emits the new tag in
   ``check-placeholder-comments.py`` and the README's status
   reference. The CLI's ``choices=`` list and every test that
   iterates :data:`DELETED_SOURCES` will pick up the new tag for
   free.
"""

from __future__ import annotations


# Provenance-tag → human-readable reason template. Keys are the
# closed vocabulary the parsers emit on ``ignored-deleted`` rows;
# values are the audit text shown to reviewers. R/C-old templates
# embed ``{new_path}`` so the audit row can name the destination —
# without it, a reviewer scanning the table would see "old path of a
# rename" with no clue *which* rename. :func:`resolve_deleted_reason`
# performs the substitution; tags without a placeholder are returned
# verbatim, so adding a new flat tag in the future stays a one-line
# change here.
DELETED_REASON: dict[str, str] = {
    "diff-D": ("git diff reported D (deleted): file removed in the "
               "diff range, no post-state to lint"),
    "changed-files-D": ("--changed-files payload row shaped `D\\tpath`: "
                        "explicit delete marker, no post-state to lint"),
    "diff-R-old": ("OLD side of a git rename (`R` row): file moved "
                   "to `{new_path}` in the diff range, no post-state "
                   "at this path to lint"),
    "diff-C-old": ("OLD (source) side of a git copy (`C` row): "
                   "duplicated to `{new_path}` in the diff range, "
                   "no modification at this path to lint"),
    "changed-files-R-old": ("OLD side of a `--changed-files` rename "
                            "row: file moved to `{new_path}`, no "
                            "post-state at this path to lint"),
    "changed-files-C-old": ("OLD (source) side of a `--changed-files` "
                            "copy row: duplicated to `{new_path}`, no "
                            "modification at this path to lint"),
}

# Reason returned by :func:`resolve_deleted_reason` for tags missing
# from :data:`DELETED_REASON`. Keeps the audit self-explanatory
# rather than crashing on a ``KeyError`` if a parser starts emitting
# a new provenance tag before this map catches up.
DELETED_REASON_FALLBACK: str = (
    "path captured as a delete by the diff intake but provenance "
    "is unknown — treated as `ignored-deleted` for safety"
)


# Closed source vocabulary surfaced by ``--list-changed-files-verbose``
# and accepted by ``--only-deleted-source``. Frozen so the CLI's
# argparse ``choices`` list, the renderer's footer-breakdown code,
# and the README's documented contract all reference one source of
# truth — adding a new tag is a one-line dict update above plus
# (deliberately) appending it here. The order is the canonical
# render order: ``D``-style tags first, then R/C-old tags grouped
# by intake (``diff-`` then ``changed-files-``) so a per-tag
# breakdown footer prints consistently across runs.
#
# The fallback message is intentionally NOT in this tuple — it's a
# safety net for parser changes that haven't propagated, not a
# value the operator can target with ``--only-deleted-source``.
DELETED_SOURCES: tuple[str, ...] = (
    "diff-D",
    "changed-files-D",
    "diff-R-old",
    "changed-files-R-old",
    "diff-C-old",
    "changed-files-C-old",
)


def resolve_deleted_reason(source: str,
                           new_path: "str | None" = None) -> str:
    """Look up the human-readable ``reason`` for an ``ignored-deleted``
    row given its provenance ``source`` tag.

    Tags whose template embeds ``{new_path}`` (today: ``diff-R-old``,
    ``diff-C-old``, ``changed-files-R-old``, ``changed-files-C-old``)
    are formatted with the supplied destination path so the reviewer
    sees where the file went. If ``new_path`` is missing on such a
    tag (defensive — parsers always supply it today), the literal
    ``"<unknown>"`` is substituted so the row stays scannable
    instead of raising a ``KeyError`` mid-render.

    Tags without a placeholder (``diff-D``, ``changed-files-D``)
    return their template verbatim. Unknown tags fall back to
    :data:`DELETED_REASON_FALLBACK` so a future parser change
    can't crash the audit emitter.
    """
    template = DELETED_REASON.get(source, DELETED_REASON_FALLBACK)
    if "{new_path}" in template:
        return template.format(new_path=new_path or "<unknown>")
    return template


# Module-level invariant: every tag with a key in `DELETED_REASON`
# (other than nothing — the dict has no out-of-vocabulary entries
# by construction) must appear in `DELETED_SOURCES`, and vice
# versa. Asserted at import time so a typo in either collection
# is caught the first time *anything* loads this module — including
# the test suite's parity check.
assert set(DELETED_REASON) == set(DELETED_SOURCES), (
    "audit_reason_vocab: DELETED_REASON keys and DELETED_SOURCES "
    "have drifted — keep them in lockstep. "
    f"Only in DELETED_REASON: {sorted(set(DELETED_REASON) - set(DELETED_SOURCES))!r}; "
    f"only in DELETED_SOURCES: {sorted(set(DELETED_SOURCES) - set(DELETED_REASON))!r}."
)


__all__ = (
    "DELETED_REASON",
    "DELETED_REASON_FALLBACK",
    "DELETED_SOURCES",
    "resolve_deleted_reason",
)
