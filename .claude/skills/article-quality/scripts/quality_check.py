#!/usr/bin/env python3
"""Mechanical quality checks for a blog post in content/blogs/.

Stdlib only, offline. Scores the structural half of the article-quality
rubric (0-35): frontmatter, summary opening, bold thesis, word count,
figure captions under each diagram block, a limits section, references,
footnotes and interlinks. The judgement half (thesis quality, evidence,
counterargument, ...) is scored by the model from references/rubric.md.

Usage:
  python3 scripts/quality_check.py <file> [--profile long|short]

Without --profile: `long` for a bundle (index.md) or more than 900 words,
`short` otherwise.
"""
import json
import os
import re
import sys

# Points per check, per profile. Each profile sums to 35.
WEIGHTS = {
    "long": {"frontmatter": 3, "summary": 5, "thesis": 3, "words": 3, "captions": 6,
             "limits": 4, "references": 5, "footnotes": 3, "interlinks": 3},
    "short": {"frontmatter": 3, "summary": 5, "thesis": 4, "words": 4, "captions": 4,
              "limits": 4, "references": 5, "footnotes": 2, "interlinks": 4},
}
WORD_RANGE = {"long": (1000, 1800), "short": (400, 700)}
MIN_REFS = {"long": 3, "short": 1}
REQUIRED_FIELDS = ["title", "date", "tags", "categories", "draft"]
BLOCKS = ["moving-diagram", "mermaid", "back-of-envelope"]

BLOCK_RE = re.compile(r"\{\{<\s*(%s)\s*>\}\}.*?\{\{<\s*/\1\s*>\}\}" % "|".join(BLOCKS), re.S)
FENCE_RE = re.compile(r"^```.*?^```", re.S | re.M)
CAPTION_RE = re.compile(r"^[*_]Figure (\d+)[:.]\s+\S.*[*_]$")
LIMITS_RE = re.compile(
    r"^##+ .*\b(when not|when .*(doesn'?t|does not|isn'?t|is not)|trade-?offs?|limits?|"
    r"limitations?|doesn'?t apply|wrong|failure modes?|caveats?|don'?t)\b", re.I)
REFS_RE = re.compile(r"^## +(references|further reading|sources)\b", re.I)
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)\s]+)[^)]*\)")


def split_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return (m.group(1), text[m.end():]) if m else ("", text)


def prose_of(body):
    """Body with diagram blocks and code fences removed."""
    return FENCE_RE.sub("", BLOCK_RE.sub("", body))


def paragraphs(prose):
    """Plain prose paragraphs: skips headings, lists, tables, quotes, shortcodes."""
    out = []
    for chunk in re.split(r"\n\s*\n", prose):
        chunk = chunk.strip()
        if not chunk or re.match(r"^(#|[-*+] |\d+\. |\||>|\{\{|\[\^)", chunk):
            continue
        out.append(chunk)
    return out


def words(s):
    return len(re.findall(r"[A-Za-z0-9][\w'’.-]*", s))


def check(cid, ok, points, weight, detail):
    return {"id": cid, "ok": ok, "points": round(points * weight, 1), "max": weight, "detail": detail}


def run(path, profile):
    text = open(path, encoding="utf-8").read()
    fm, body = split_frontmatter(text)
    prose = prose_of(body)
    w = WEIGHTS[profile]
    checks = []

    # Frontmatter fields, and mermaid flag set exactly when a mermaid block exists.
    missing = [f for f in REQUIRED_FIELDS if not re.search(r"^%s:" % f, fm, re.M)]
    has_mermaid = bool(re.search(r"\{\{<\s*mermaid\s*>\}\}", body))
    flag = bool(re.search(r"^mermaid:\s*true", fm, re.M))
    problems = (["missing " + ", ".join(missing)] if missing else []) + \
        (["mermaid flag doesn't match mermaid blocks"] if has_mermaid != flag else [])
    checks.append(check("frontmatter", not problems, 0 if problems else 1, w["frontmatter"],
                        "; ".join(problems) or "ok"))

    # Summary: the intro before the first H2 (paragraphs and lists) carries >= 60 words.
    before_h2 = re.split(r"^## ", prose, maxsplit=1, flags=re.M)[0]
    n = words(before_h2)
    checks.append(check("summary", n >= 60, min(n / 60, 1), w["summary"],
                        "intro before the first H2 has %d words (need 60)" % n))

    # Bold thesis: a bolded phrase of 5+ words in the first 3 prose paragraphs.
    early = paragraphs(prose)[:3]
    bolds = [b for p in early for b in re.findall(r"\*\*([^*]+)\*\*", p) if words(b) >= 5]
    checks.append(check("thesis", bool(bolds), 1 if bolds else 0, w["thesis"],
                        "bold thesis: " + bolds[0][:80] if bolds else "no bolded claim (5+ words) in the first 3 paragraphs"))

    # Word count of the prose, with partial credit within 20% of the range.
    lo, hi = WORD_RANGE[profile]
    n = words(prose)
    pts = 1 if lo <= n <= hi else 0.5 if lo * 0.8 <= n <= hi * 1.2 else 0
    checks.append(check("words", pts == 1, pts, w["words"], "%d prose words (target %d-%d)" % (n, lo, hi)))

    # Captions: the next non-blank line after each block is "*Figure N: ...*", numbered in order.
    blocks = list(BLOCK_RE.finditer(body))
    good, bad, expect = 0, [], 1
    for b in blocks:
        nxt = next((l.strip() for l in body[b.end():].splitlines() if l.strip()), "")
        m = CAPTION_RE.match(nxt)
        if m and int(m.group(1)) == expect:
            good += 1
        else:
            bad.append("%s #%d" % (b.group(1), blocks.index(b) + 1))
        expect += 1
    pts = good / len(blocks) if blocks else 1
    checks.append(check("captions", not bad, pts, w["captions"],
                        "uncaptioned or misnumbered: " + ", ".join(bad) if bad else
                        "%d blocks captioned" % len(blocks) if blocks else "no diagram blocks"))

    # Limits: a heading about when not to use it, trade-offs or failure modes.
    heads = [l for l in prose.splitlines() if LIMITS_RE.match(l)]
    checks.append(check("limits", bool(heads), 1 if heads else 0, w["limits"],
                        heads[0].lstrip("# ") if heads else "no 'when not to use / trade-offs / limits' heading"))

    # References: a References / Further reading H2 with enough links.
    lines, refs, inside = body.splitlines(), 0, False
    for l in lines:
        if l.startswith("## "):
            inside = bool(REFS_RE.match(l))
        elif inside:
            refs += len(LINK_RE.findall(l))
    need = MIN_REFS[profile]
    checks.append(check("references", refs >= need, min(refs / need, 1), w["references"],
                        "%d links under References/Further reading (need %d)" % (refs, need)))

    # Footnotes: at least one [^x] reference with a matching definition.
    defs = set(re.findall(r"^\[\^([^\]]+)\]:", prose, re.M))
    used = set(re.findall(r"\[\^([^\]]+)\](?!:)", prose))
    paired, orphans = used & defs, used ^ defs
    checks.append(check("footnotes", bool(paired) and not orphans, 1 if paired and not orphans else 0.5 if paired else 0,
                        w["footnotes"], "%d footnotes" % len(paired) + ("; unmatched: " + ", ".join(sorted(orphans)) if orphans else "")))

    # Interlinks: relative links to other notes, and no [[wikilinks]].
    rel = [u for u in LINK_RE.findall(prose) if not re.match(r"^(https?:|mailto:|#)", u)]
    rel += re.findall(r"\{\{<\s*ref\s", prose)
    wiki = re.findall(r"\[\[[^\]]+\]\]", prose)
    pts = (1 if rel else 0) * (0 if wiki else 1)
    checks.append(check("interlinks", pts == 1, pts, w["interlinks"],
                        "%d relative links" % len(rel) + ("; wikilinks render as text: %d" % len(wiki) if wiki else "")))

    total = round(sum(c["points"] for c in checks), 1)
    return {"file": path, "profile": profile, "mechanical": total, "max": 35, "checks": checks}


def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        sys.exit(__doc__)
    path, profile = args[0], None
    if "--profile" in args:
        profile = args[args.index("--profile") + 1]
        if profile not in WEIGHTS:
            sys.exit("--profile must be long or short")
    if profile is None:
        _, body = split_frontmatter(open(path, encoding="utf-8").read())
        bundle = os.path.basename(path) == "index.md"
        profile = "long" if bundle or words(prose_of(body)) > 900 else "short"
    print(json.dumps(run(path, profile), indent=2))


if __name__ == "__main__":
    main()
