"""The one list of non-canonical snapshot and duplicate trees (CLAUDE.md).

Two repo-wide markdown walkers each carried a private exclusion list, and
the lists diverged in both mechanism (substring-on-relpath vs path-parts)
and content: the profile-claims walker excluded stale git worktrees under
`.claude/worktrees/` while the records-currency walker did not, so one
guard was immune to a stale checkout that tripped the other (probed live
during the PR #8 second review). Every walker that skips non-current
trees imports this module; `test_snapshot_exclusions.py` pins the shape
and pins that neither walker grows a private list again.
"""

from pathlib import Path

# Directory names excluded wherever they appear as a path component.
SNAPSHOT_DIR_PARTS = frozenset(
    {
        ".tmp",
        "bundles",
        "dist",
        "__pycache__",
        ".git",
        "node_modules",
        # Gitignored private session records: a local-only markdown file
        # must not trip a public guard on a local battery run (apparatus
        # audit, 2026-08-10).
        "local",
    }
)

# Path-component prefixes, for tree classes a bare name cannot express:
# release/package-<version> directories and pytest-cache-files-* dirs.
SNAPSHOT_PART_PREFIXES = (
    "package-",
    "pytest-cache",
    "pytest-work",
)


def is_snapshot_path(rel) -> bool:
    """True when the repo-relative path sits inside a non-canonical tree.

    `.claude/worktrees` is matched as the consecutive pair, never as a
    blanket exclusion of `.claude/`, so agent-config markdown stays
    scanned while stale worktree checkouts do not.
    """
    parts = Path(rel).parts
    if any(part in SNAPSHOT_DIR_PARTS for part in parts):
        return True
    # Prefixes describe DIRECTORY classes (package-v1.1.23/,
    # pytest-cache-files-*/), so the filename component is exempt: a future
    # docs/package-layout.md is canonical, its directory namesake is not.
    if any(
        part.startswith(prefix)
        for part in parts[:-1]
        for prefix in SNAPSHOT_PART_PREFIXES
    ):
        return True
    for index in range(len(parts) - 1):
        if parts[index] == ".claude" and parts[index + 1] == "worktrees":
            return True
    return False
