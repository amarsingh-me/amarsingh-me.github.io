#!/usr/bin/env python3
"""Local AI-content scorer for resumes (.tex) and hiring messages (.md/.txt).

Stdlib only, offline. Scores 0-100 (higher = more AI-like) from stylometric
tells that detectors like ZeroGPT/GPTZero react to: uniform sentence length
(low burstiness), stock phrases, rule-of-three lists, colon/semicolon pivots,
participial tails, repeated openers, negative parallelism ("not X, but Y"),
ta-da openers, superficial "-ing" analysis, and the vocabulary and chatbot
artifacts listed in references/ai-tells.md (Wikipedia "Signs of AI
writing" plus 2026 lists). It approximates those tools; it does not reproduce
them.

Usage:
  python3 scripts/ai_detect.py <file> [--md]
"""
import json
import re
import statistics
import sys

# (regex, weight). Weights are per hit, summed per sentence and capped at 1.0.
STOCK_PHRASES = [
    (r"\breach(ing)? out\b", 0.5),
    (r"\bwanted to\b", 0.3),
    (r"\bI'?d (welcome|love)\b", 0.5),
    (r"\bwelcome (a|the) (short|brief|quick)\b", 0.4),
    (r"\bkeen to\b", 0.4),
    (r"\bgo deep\b", 0.4),
    (r"\bcarr(y|ies) over\b", 0.4),
    (r"\bthe things? .{1,30} needs? most\b", 0.6),
    (r"\bevery day\b", 0.3),
    (r"\bthanks? (you )?for your time\b", 0.3),
    (r"\bcomfortable with\b", 0.3),
    (r"\b(looks like|be) a (good |strong |great )?fit\b", 0.4),
    (r"\bproven track record\b", 0.5),
    (r"\btrack record\b", 0.3),
    (r"\bleverag", 0.4),
    (r"\bspearhead", 0.5),
    (r"\bpassionate\b", 0.5),
    (r"\bexcited\b", 0.4),
    (r"\bthrilled\b", 0.5),
    (r"\bseamless", 0.5),
    (r"\brobust\b", 0.4),
    (r"\bend-to-end\b", 0.25),
    (r"\b(at|internet) scale\b", 0.3),
    (r"\b(drive|driving|drove)\b", 0.2),
    (r"\bstrong (track|background|foundation|grounding)\b", 0.3),
    (r"\bdeep(ly)? (expertise|experience|dive|understanding)\b", 0.3),
    (r"\bhands-on\b", 0.2),
    (r"\bI believe\b", 0.3),
    (r"\balign(s|ed)? (well |closely )?with\b", 0.4),
    (r"\bcutting-edge\b", 0.5),
    (r"\bfast-paced\b", 0.4),
    (r"\bresults-driven\b", 0.5),
    (r"\bsynerg", 0.5),
    (r"\bproduction-grade\b", 0.3),
    (r"\bmission-critical\b", 0.3),
    (r"\bmeasurable\b", 0.3),
    (r"\bstreamlin", 0.3),
    (r"\belevat", 0.4),
    (r"\bfoster", 0.4),
    (r"\bempower", 0.4),
    (r"\bnavigat", 0.3),
    (r"\blandscape\b", 0.4),
    (r"\bjourney\b", 0.4),
    (r"\bdelve", 0.6),
    (r"\bshowcas", 0.4),
    (r"\bI'?m confident\b", 0.4),
    (r"\blook(ing)? forward\b", 0.3),
    (r"\bnot only\b.{1,60}\bbut also\b", 0.5),
    (r"\bcore (skills|strengths)\b", 0.4),
    (r"\bstrict\b", 0.2),
    (r"\bproblems I\b", 0.3),
    (r"\bcomplex\b", 0.2),
    (r"\bensur(e|ing)\b", 0.25),
    (r"\bdirectly\b", 0.2),
    (r"\b(key|critical|pivotal|crucial|vital)\b", 0.2),
    # Wikipedia "Signs of AI writing" vocabulary and 2026 tell lists
    # (see references/ai-tells.md). Filler words that collide with normal
    # resume wording (real-time, held, shape, signal) only match as phrases.
    (r"\b(tapestry|testament|interplay|beacon|linchpin|paradigm)\b", 0.5),
    (r"\bintricac|\bintricate\b", 0.4),
    (r"\bunderscor", 0.5),
    (r"\b(bolster|garner)", 0.4),
    (r"\bmeticulous", 0.5),
    (r"\b(vibrant|enduring|multifaceted|holistic|profound|invaluable)\b", 0.4),
    (r"\b(realm|cornerstone|paramount)\b", 0.4),
    (r"\b(groundbreaking|game-?changer|transformative|revolutioni[sz]e)\b", 0.5),
    (r"\b(harness|unlock|unleash|embark)", 0.3),
    (r"\bresonat", 0.4),
    (r"\bever-evolving\b", 0.5),
    (r"\bstate-of-the-art\b", 0.3),
    (r"\b(quietly|fundamentally|remarkably|arguably|genuinely|truly|incredibly)\b", 0.4),
    (r"\bload-bearing\b|\bbuilt different\b", 0.5),
    (r"\bthe real (problem|question|issue|work|story|win)\b", 0.4),
    (r"\bmove the needle\b|\blean(ing)? into\b|\bdouble down\b", 0.4),
    (r"^(moreover|furthermore|additionally|in addition|consequently|notably|importantly|indeed)\b", 0.4),
    (r"\b(serves|serving|stands|standing) as\b", 0.4),
    (r"\bboasts?\b", 0.4),
    (r"\bit'?s (important|worth|crucial) (to note|noting|to remember)\b", 0.6),
    (r"\bneedless to say\b|\binterestingly\b", 0.4),
    (r"\b(plays?|playing) an? (vital|pivotal|key|crucial|significant) role\b", 0.6),
    (r"\blasting impact\b|\bsignificant milestone\b|\bat the forefront\b|\bsetting the stage\b", 0.5),
    (r"\b(nestled|breathtaking|must-visit|hidden gem|world-class|renowned)\b", 0.5),
    (r"\bin today'?s\b|\bin a world where\b|\bimagine a world\b", 0.6),
    (r"\bthink of it as\b|\bat its core\b|\bwhen it comes to\b", 0.4),
    (r"\blet'?s (dive|delve|break it down|unpack)\b|\bbuckle up\b", 0.6),
    (r"\b(experts|observers|studies|industry reports?) (say|suggest|note|show|argue)\b", 0.5),
    (r"\bmany believe\b|\bwidely recogni[sz]ed\b", 0.4),
    (r"\bthis changes everything\b|\bparadigm shift\b", 0.6),
    (r"\band that'?s (okay|ok)\b|\byou'?re not alone\b", 0.5),
    (r"^(in summary|in conclusion|overall|ultimately|all in all|at the end of the day|the bottom line)\b", 0.6),
    (r"\bI hope this helps\b|\blet me know if\b|\bfeel free to\b|\bwould you like me to\b", 0.6),
    (r"^(certainly|absolutely|of course|great question)\b", 0.6),
    (r"\bas of my (last|knowledge)\b|\bas an AI\b", 1.0),
    (r"\[(your name|company|name|date)\]|\bINSERT\b", 1.0),
    (r"utm_source=chatgpt|oaicite|contentReference|turn0search", 1.0),
]

NEG_PARALLEL = re.compile(
    r"\b(it'?s|this is|that'?s)? ?not (just |only |about |merely )?[^.;]{1,40}[,;.] "
    r"(it'?s|but|this is)\b|\bisn'?t about\b|\bless [a-z]+, more [a-z]+\b",
    re.I,
)
TA_DA = re.compile(
    r"here'?s (the (thing|kicker|truth|catch)|what nobody)|the result\?|"
    r"the best part\?|let that sink in|the uncomfortable truth|spoiler:|plot twist",
    re.I,
)
SUPERFICIAL_ING = re.compile(
    r",\s+(highlighting|underscoring|reflecting|contributing to|paving the way|"
    r"cementing|showcasing|emphasizing|demonstrating|solidifying)\b",
    re.I,
)

TRIPLET = re.compile(r",[^,.;:]{1,45},\s*(and|or)\s", re.I)
PIVOT = re.compile(r"(;|:\s)")
PARTICIPIAL_TAIL = re.compile(
    r",\s+(cutting|ensuring|delivering|enabling|improving|reducing|driving|"
    r"resulting|leading|allowing|streamlining|while|making|helping|becoming)\b",
    re.I,
)
EM_DASH = re.compile("\u2014")

SKIP_LINE = re.compile(
    r"^(hi|hello|dear)\b|^(best|kind|warm)?\s*regards|^thanks,?$|^cheers|"
    r"^amar singh$|linkedin\.com|^\+?\d[\d ]{6,}|^(\*\*)?subject:",
    re.I,
)


def strip_latex(s):
    s = s.replace("$\\to$", " to ").replace("\u2192", " to ")
    s = s.replace("\\%", "%").replace("\\&", "&").replace("--", "-")
    s = re.sub(r"\\(begin|end|vspace|hspace)\{[^{}]*\}", " ", s)
    s = re.sub(r"\\[a-zA-Z]+=\d+", " ", s)  # \hyphenpenalty=10000 etc.
    for _ in range(3):
        s = re.sub(r"\\[a-zA-Z]+\*?\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\[a-zA-Z]+\*?", " ", s)
    s = s.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", s).strip()


def units_from_tex(text):
    body = re.sub(r"(?m)^\s*%.*$", "", text)
    units = []
    summ = re.search(r"\\section\{Professional Summary\}(.*?)\\section\{", body, re.S)
    if summ:
        units += split_sentences(strip_latex(summ.group(1)))
    # all \item bullets except Certifications
    cert = re.search(r"\\section\{Certifications\}.*?\\end\{highlights\}", body, re.S)
    if cert:
        body = body.replace(cert.group(0), "")
    for m in re.finditer(r"\\item(.*?)(?=\\item|\\end\{highlights\})", body, re.S):
        t = strip_latex(m.group(1))
        t = re.sub(r"^[A-Z][\w\u00C0-\u017F]*:\s+", "", t)  # "Zenika: ..." label
        if t:
            units.append(t)
    return units


def split_sentences(par):
    par = par.strip()
    if not par:
        return []
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", par)
    return [p.strip() for p in parts if len(p.split()) >= 2]


def units_from_md(text):
    units = []
    for par in re.split(r"\n\s*\n", text):
        lines = [l.strip() for l in par.splitlines() if l.strip()]
        lines = [l for l in lines if not SKIP_LINE.search(l)]
        if not lines:
            continue
        clean = re.sub(r"\*\*|__|`", "", " ".join(lines))
        units += split_sentences(clean)
    return units


def score_unit(u):
    reasons, s = [], 0.0
    for pat, w in STOCK_PHRASES:
        m = re.search(pat, u, re.I)
        if m:
            s += w
            reasons.append(f'stock phrase "{m.group(0)}"')
    n = len(TRIPLET.findall(u))
    if n:
        s += 0.3 * n
        reasons.append(f"rule-of-three list x{n}")
    n = len(PIVOT.findall(u))
    if n:
        s += 0.2 * n
        reasons.append(f"colon/semicolon pivot x{n}")
    m = PARTICIPIAL_TAIL.search(u)
    if m:
        s += 0.3
        reasons.append(f'participial tail ", {m.group(1)}"')
    m = SUPERFICIAL_ING.search(u)
    if m:
        s += 0.4
        reasons.append(f'superficial -ing analysis ", {m.group(1)}"')
    if NEG_PARALLEL.search(u):
        s += 0.5
        reasons.append("negative parallelism (not X, but Y)")
    m = TA_DA.search(u)
    if m:
        s += 0.5
        reasons.append(f'ta-da opener "{m.group(0)}"')
    if EM_DASH.search(u):
        s += 0.4
        reasons.append("em dash")
    words = len(u.split())
    if 18 <= words <= 32:
        s += 0.15
        reasons.append(f"mid-length template sentence ({words}w)")
    return min(s, 1.0), reasons


def burstiness(units):
    lens = [len(u.split()) for u in units]
    if len(lens) < 3:
        return 0.5, 0.0
    cv = statistics.pstdev(lens) / statistics.mean(lens)
    # human prose usually cv >= 0.6; AI prose clusters around 0.2-0.4
    return max(0.0, min(1.0, (0.65 - cv) / 0.4)), cv


def opener_repetition(units):
    firsts = [u.split()[0].lower().strip(",.") for u in units if u.split()]
    if len(firsts) < 3:
        return 0.0
    top = max(firsts.count(f) for f in set(firsts))
    i_ratio = sum(f in ("i", "i've", "i'm", "i'd") for f in firsts) / len(firsts)
    return min(1.0, max((top - 1) / len(firsts) * 2, i_ratio * 1.5))


def analyze(path):
    text = open(path, encoding="utf-8").read()
    units = units_from_tex(text) if path.endswith(".tex") else units_from_md(text)
    scored = [(u, *score_unit(u)) for u in units]
    mean_unit = statistics.mean(s for _, s, _ in scored) if scored else 0.0
    burst, cv = burstiness(units)
    opener = opener_repetition(units)
    hit_ratio = sum(1 for _, s, _ in scored if s >= 0.4) / max(1, len(scored))
    overall = 100 * min(1.0, 0.30 * burst + 0.35 * mean_unit + 0.10 * opener + 0.25 * hit_ratio) / 0.65
    overall = round(min(100.0, overall))
    level = "High AI" if overall >= 60 else "Mixed" if overall >= 31 else "Likely human"
    flagged = [
        {"text": u, "score": round(s * 100), "reasons": r}
        for u, s, r in sorted(scored, key=lambda x: -x[1])
        if s >= 0.4
    ]
    return {
        "file": path,
        "overall": overall,
        "level": level,
        "signals": {
            "burstiness_penalty": round(burst * 100),
            "sentence_length_cv": round(cv, 2),
            "mean_sentence_score": round(mean_unit * 100),
            "flagged_sentence_ratio": round(hit_ratio * 100),
            "opener_repetition": round(opener * 100),
        },
        "units": len(units),
        "flagged": flagged,
    }


def to_md(r):
    out = [
        f"**AI-content score: {r['overall']}/100 ({r['level']})** for `{r['file']}`",
        "",
        "| Signal | Value |",
        "|---|---|",
    ]
    out += [f"| {k} | {v} |" for k, v in r["signals"].items()]
    out += ["", f"Flagged sentences ({len(r['flagged'])} of {r['units']}):", ""]
    for f in r["flagged"]:
        out.append(f"- [{f['score']}] {f['text']}")
        out.append(f"  - {'; '.join(f['reasons'])}")
    return "\n".join(out)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    res = analyze(sys.argv[1])
    print(to_md(res) if "--md" in sys.argv else json.dumps(res, indent=2))
