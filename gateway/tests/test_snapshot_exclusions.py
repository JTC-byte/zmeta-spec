"""Pins for the single-sourced snapshot-tree exclusion list.

The stale-worktree carve-out shipped in PR #8 with no in-repo
reproduction: the state it suppresses (a git worktree under
`.claude/worktrees/` carrying its own copy of the repository's docs)
existed only as a session act, which is the vacuous-verification class
(P2-D1). These tests are the in-repo artifact: the exact path shape is
pinned excluded, the canonical tree is pinned included (the non-vacuity
floor), and both repo-wide markdown walkers are pinned to the shared
module so the two lists cannot silently diverge again.
"""

from pathlib import Path

from snapshot_exclusions import is_snapshot_path


ROOT = Path(__file__).resolve().parents[2]
WALKER_FILES = (
    "gateway/tests/test_governed_doc_claims.py",
    "gateway/tests/test_records_claim_currency.py",
)


def test_the_stale_worktree_shape_is_excluded():
    """The PR #8 carve-out's exact reproduction shape, pinned in-repo."""
    assert is_snapshot_path(".claude/worktrees/wf_probe/docs/stale.md")
    assert is_snapshot_path(".claude/worktrees/x/README.md")


def test_dot_claude_is_not_blanket_excluded():
    """Only the worktrees subtree is non-canonical, not agent config."""
    assert not is_snapshot_path(".claude/notes.md")
    assert not is_snapshot_path(".claude/agents/reviewer.md")


def test_every_snapshot_tree_class_is_excluded():
    for rel in (
        ".tmp/release_v1_1_6_edge/README.md",
        "release/bundles/zmeta-edge/README.md",
        "release/dist/docs/README.md",
        "release/package-v1.1.23/RELEASE_NOTES.md",
        "pytest-cache-files-abc123/doc.md",
        "local/private_checkpoint.md",
        "node_modules/pkg/README.md",
    ):
        assert is_snapshot_path(rel), rel


def test_the_canonical_tree_is_not_excluded():
    """Non-vacuity floor: the guard must still see the real stack."""
    for rel in (
        "README.md",
        "docs/zmeta_change_governance.md",
        "adapters/AUTHORING.md",
        "adapters/mapping-packs/edge-comms-bladerf/README.md",
        "release/README.md",
        "conformance/profile-projection/README.md",
    ):
        assert not is_snapshot_path(rel), rel


def test_prefix_rules_scope_to_directories_not_filenames():
    """A plausible future document must not vanish from both walkers.

    The first draft scanned every path component including the basename,
    so docs/package-layout.md was silently excluded (pre-cut attack pass).
    The prefixes describe directory classes; a file NAME starting with one
    is canonical.
    """
    assert not is_snapshot_path("docs/package-layout.md")
    assert not is_snapshot_path("docs/pytest-cache-notes.md")
    assert is_snapshot_path("release/package-v1.1.23/RELEASE_NOTES.md")
    assert is_snapshot_path("pytest-work/tool-floors-x/scratch.md")


def test_both_markdown_walkers_use_the_shared_list():
    """Neither walker may grow a private exclusion list again.

    Source-level pin, matching the checklist-flag convention: each walker
    file must call the shared predicate, and the retired private lists
    (the substring tuple and _IGNORED_PARTS) must not reappear.
    """
    for rel in WALKER_FILES:
        source = (ROOT / rel).read_text(encoding="utf-8")
        assert "is_snapshot_path(" in source, f"{rel} no longer calls the shared predicate"
        assert "_IGNORED_PARTS" not in source, f"{rel} regrew a private exclusion set"
        assert '"release/dist"' not in source, f"{rel} regrew the private substring tuple"
