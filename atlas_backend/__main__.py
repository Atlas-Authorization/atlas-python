"""``python -m atlas_backend doctor``: run the environment checks and exit 1 when one fails."""

from __future__ import annotations

import sys

from ._doctor import doctor


def main(argv: list[str]) -> int:
    if argv[:1] != ["doctor"]:
        print("usage: python -m atlas_backend doctor  (reads ATLAS_SECRET_KEY, ATLAS_API_URL, ATLAS_JWKS_URL, ATLAS_ISSUER)")
        return 2
    report = doctor()
    print(report.format())
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
