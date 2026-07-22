"""Published-checksum immutability pin (R1-11 second-glance item).

release/SHA256SUMS_<version>.txt represents the assets published at that
release and must never be rewritten by post-release main commits
(AGENTS.md release limits; the R1-10 second-glance register flagged that
no machine check pinned this). Each file is compared byte-for-byte
against its own release tag's blob.

Honest scope note: in a shallow or tagless checkout (e.g. default CI
fetch-depth 1) no tags are available, so only the corpus floor runs
there; the full check executes wherever the mandated local kernel gate
and the release battery run — a full clone with tags.
"""

import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _git(*args):
    result = subprocess.run(
        ["git", *args], cwd=str(ROOT), capture_output=True
    )
    return result.returncode, result.stdout


class PublishedChecksumImmutabilityTest(unittest.TestCase):
    def test_published_checksum_files_match_their_release_tags(self):
        files = sorted(ROOT.glob("release/SHA256SUMS_v*.txt"))
        # Honest scope of this floor (R1-11 A-26): it is a sanity check that
        # the glob found a corpus at all, NOT a deletion detector - 13 of
        # the 19 present files could be removed and it would still pass.
        # That is deliberate: the published record lives in the annotated
        # tags (compared per file below), not in the working tree, and
        # deriving the expected set from tags instead would make this test
        # vacuous in the tagless/shallow checkout the floor exists for.
        self.assertGreaterEqual(
            len(files),
            6,
            "no published checksum corpus found in release/ - the glob or the "
            "checkout is wrong (this floor is a corpus-presence sanity check, "
            "not a deletion detector; immutability is enforced per file "
            "against each release tag below)",
        )

        code, out = _git("tag", "-l", "v*")
        tags = set(out.decode().split()) if code == 0 else set()

        checked = 0
        for path in files:
            match = re.fullmatch(r"SHA256SUMS_(v[0-9.]+)\.txt", path.name)
            self.assertIsNotNone(match, path.name)
            tag = match.group(1)
            if tag not in tags:
                continue
            code, tagged_bytes = _git("show", f"{tag}:release/{path.name}")
            if code != 0:
                # Tag predates the checksum file layout; nothing published
                # under this name at that tag to compare against.
                continue
            working = path.read_bytes()
            self.assertEqual(
                tagged_bytes.replace(b"\r\n", b"\n"),
                working.replace(b"\r\n", b"\n"),
                f"{path.name} differs from its published blob at tag {tag}: "
                "published checksums are immutable - a divergence must be a "
                "new release cut, never a rewrite",
            )
            checked += 1

        if tags:
            self.assertGreater(
                checked, 0,
                "tags are present but no checksum file could be compared - "
                "the immutability check has gone vacuous",
            )


if __name__ == "__main__":
    unittest.main()
