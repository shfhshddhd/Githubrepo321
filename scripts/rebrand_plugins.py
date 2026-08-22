"""Replace upstream branding only inside string and comment tokens.

Identifiers such as CipherElite, rishabh, Config, CMD_LIST, and ELITE_SESSION
are intentionally never modified by this script.
"""

from __future__ import annotations

import io
import re
import sys
import tokenize
from pathlib import Path


REPLACEMENTS = (
    ("https://github.com/rishabhops/CipherElite", ""),
    ("https://t.me/cipherelite_support", ""),
    ("https://t.me/THANOS_PRO", ""),
    ("https://t.me/thanosprosss", ""),
    ("https://t.me/thanosceo", ""),
    ("@thanosceo", ""),
    ("@THANOS_PRO", ""),
    ("@rishabhops", ""),
    ("CIPHER ELITE", "FLEX FUCKER USERBOT"),
    ("Cipher Elite", "FLEX FUCKER USERBOT"),
    ("CipherElite", "FLEX FUCKER USERBOT"),
)


def _replace_token(token: tokenize.TokenInfo) -> tokenize.TokenInfo:
    string_types = {tokenize.STRING, tokenize.COMMENT}
    fstring_middle = getattr(tokenize, "FSTRING_MIDDLE", None)
    if fstring_middle is not None:
        string_types.add(fstring_middle)
    if token.type not in string_types:
        return token
    value = token.string
    for old, new in REPLACEMENTS:
        value = value.replace(old, new)
    # Only replace standalone visible branding. Underscored compatibility
    # names such as ELITE_SESSION and ELITE_BOT_PREFIX are environment keys.
    value = re.sub(r"\bCipher\b", "FLEX", value)
    value = re.sub(r"\bElite\b", "FLEX FUCKER USERBOT", value)
    value = re.sub(r"\bCIPHER\b", "FLEX", value)
    value = re.sub(r"\bELITE\b", "FLEX FUCKER USERBOT", value)
    return token._replace(string=value)


def rebrand_file(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    tokens = tokenize.generate_tokens(io.StringIO(source).readline)
    rewritten = tokenize.untokenize(_replace_token(token) for token in tokens)
    path.write_text(rewritten, encoding="utf-8")


def main() -> None:
    roots = [Path(value) for value in sys.argv[1:]]
    if not roots:
        roots = [Path("telegram_userbot/plugins"), Path("telegram_userbot/utils")]
    files = [
        path
        for root in roots
        for path in (root.rglob("*.py") if root.is_dir() else [root])
        if path.is_file()
    ]
    for path in files:
        rebrand_file(path)
    print(f"Rebranded {len(files)} Python file(s) without changing identifiers.")


if __name__ == "__main__":
    main()
