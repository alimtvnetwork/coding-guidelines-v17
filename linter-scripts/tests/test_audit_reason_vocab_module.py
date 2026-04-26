"""Single-source-of-truth contract for the `ignored-deleted` vocabulary.

The placeholder linter and its test suite must reference the *same*
provenance tags and reason templates — a typo in either location
silently desynchronises the audit contract and (worse) hides itself
behind a passing assertion that compares two independently-typed
copies of the same string.

The shared module ``linter-scripts/audit_reason_vocab.py`` exists to
make that drift impossible: the linter imports its constants from
there, and these tests assert object identity (not equality) between
the linter's underscored re-exports and the canonical module's
public names. If a future refactor accidentally redefines a constant
inline inside ``check-placeholder-comments.py``, the identity check
fails immediately — no silent drift can sneak past code review.

This file is hermetic: it only inspects in-process module state, no
subprocesses or filesystem fixtures.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from conftest_shim import (  # noqa: E402
    load_audit_reason_vocab,
    load_placeholder_linter,
)


_MOD = load_placeholder_linter()
_VOCAB = load_audit_reason_vocab()


class SharedVocabularyIdentity(unittest.TestCase):
    """Linter re-exports must be the *same objects* as the vocab module."""

    def test_deleted_reason_dict_is_shared(self) -> None:
        # Identity, not equality — a future refactor that shadowed the
        # re-export with an inline copy would still pass `==` but
        # break the single-source-of-truth guarantee. `is` makes the
        # invariant unambiguous.
        self.assertIs(_MOD._DELETED_REASON, _VOCAB.DELETED_REASON)

    def test_deleted_sources_tuple_is_shared(self) -> None:
        self.assertIs(_MOD._DELETED_SOURCES, _VOCAB.DELETED_SOURCES)

    def test_fallback_string_is_shared(self) -> None:
        self.assertIs(_MOD._DELETED_REASON_FALLBACK,
                      _VOCAB.DELETED_REASON_FALLBACK)

    def test_resolve_function_is_shared(self) -> None:
        self.assertIs(_MOD._resolve_deleted_reason,
                      _VOCAB.resolve_deleted_reason)


class VocabularyShapeInvariants(unittest.TestCase):
    """Internal-consistency checks the import-time assert also enforces.

    Duplicated here as explicit unit tests so a regression surfaces
    with a readable test name in CI rather than as a cryptic
    ``AssertionError`` from the module-level guard.
    """

    def test_keys_match_sources_set(self) -> None:
        self.assertEqual(set(_VOCAB.DELETED_REASON),
                         set(_VOCAB.DELETED_SOURCES))

    def test_sources_tuple_has_no_duplicates(self) -> None:
        # Tuple — not set — to preserve render order in the footer
        # breakdown. The deduplication invariant is asserted here so
        # an accidental copy/paste in the canonical list trips a
        # named test instead of corrupting the breakdown counts.
        self.assertEqual(len(_VOCAB.DELETED_SOURCES),
                         len(set(_VOCAB.DELETED_SOURCES)))

    def test_fallback_is_not_in_sources_vocabulary(self) -> None:
        # The fallback message is a safety net for parser drift, not
        # an operator-targetable value. If it ever leaks into
        # ``DELETED_SOURCES`` the CLI would offer it as a
        # ``--only-deleted-source`` choice — surprising and wrong.
        self.assertNotIn(_VOCAB.DELETED_REASON_FALLBACK,
                         _VOCAB.DELETED_SOURCES)
        # Also: no key in the reason dict equals the fallback value
        # (would mean a real tag accidentally shares the safety-net
        # text and reviewers couldn't tell them apart in the audit).
        self.assertNotIn(_VOCAB.DELETED_REASON_FALLBACK,
                         _VOCAB.DELETED_REASON.values())


class ResolveDeletedReasonContract(unittest.TestCase):
    """Public-API behaviour of `resolve_deleted_reason`, exercised on the
    canonical module directly (not the linter re-export) so the test
    documents the shared module as the contract owner.
    """

    def test_flat_tag_returns_template_verbatim(self) -> None:
        # ``diff-D`` has no ``{new_path}`` placeholder — supplying
        # one must NOT cause string formatting / leak the value.
        self.assertEqual(
            _VOCAB.resolve_deleted_reason("diff-D",
                                          new_path="ignored.md"),
            _VOCAB.DELETED_REASON["diff-D"],
        )

    def test_placeholder_tag_substitutes_new_path(self) -> None:
        msg = _VOCAB.resolve_deleted_reason(
            "diff-R-old", new_path="spec/dest.md")
        self.assertIn("`spec/dest.md`", msg)
        self.assertNotIn("{new_path}", msg)

    def test_placeholder_tag_without_new_path_uses_unknown(self) -> None:
        msg = _VOCAB.resolve_deleted_reason("changed-files-C-old")
        self.assertIn("<unknown>", msg)
        self.assertNotIn("{new_path}", msg)

    def test_unknown_tag_returns_fallback(self) -> None:
        self.assertEqual(
            _VOCAB.resolve_deleted_reason("brand-new-future-tag"),
            _VOCAB.DELETED_REASON_FALLBACK,
        )


class CanonicalRenderOrder(unittest.TestCase):
    """The tuple's order is part of the contract — pin it explicitly so
    a reorder here forces a deliberate review (and a README update).
    """

    def test_d_tags_precede_r_c_old_tags(self) -> None:
        order = list(_VOCAB.DELETED_SOURCES)
        # All ``-D`` tags must appear before any ``-old`` tag so the
        # footer breakdown reads "deletes first, then renames /
        # copies". Catches an accidental sort or shuffle.
        last_d = max(i for i, s in enumerate(order) if s.endswith("-D"))
        first_old = min(i for i, s in enumerate(order)
                        if s.endswith("-old"))
        self.assertLess(last_d, first_old)

    def test_diff_intake_precedes_changed_files_within_each_kind(self) -> None:
        # Within each "kind" (D, R-old, C-old), the ``diff-`` tag
        # comes before the ``changed-files-`` tag. Mirrors the
        # documented render order in the README's status reference.
        order = list(_VOCAB.DELETED_SOURCES)
        for suffix in ("-D", "-R-old", "-C-old"):
            diff_tag = f"diff{suffix}"
            cf_tag = f"changed-files{suffix}"
            self.assertIn(diff_tag, order)
            self.assertIn(cf_tag, order)
            self.assertLess(order.index(diff_tag), order.index(cf_tag),
                            f"`{diff_tag}` must come before `{cf_tag}`")


if __name__ == "__main__":
    unittest.main()
