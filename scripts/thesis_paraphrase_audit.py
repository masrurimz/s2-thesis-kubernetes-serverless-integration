#!/usr/bin/env python3
"""Multi-tier verbatim/paraphrase audit of the thesis against archived source papers.

Tiers (in order of determinism):
  T1  maximal n-gram overlap (k=8 flag, k=6 review) on stop-word-stripped content words
  T2  winnowing fingerprints (Schleimer et al. 2003): shared 5-gram hashes selected by
      window-min; catches distributed/reordered copying that a single LCS run misses
  T3  sentence-pair content-word Jaccard >= 0.6: same words reordered
  T4  optional semantic tier via sentence-transformers if installed (skipped otherwise)

Self-test is mandatory before any clean verdict: a verbatim plant AND a word-reordered
plant must be caught by the relevant tiers, else the run aborts with a detector error.

Usage:
  uv run python scripts/thesis_paraphrase_audit.py
  uv run python scripts/thesis_paraphrase_audit.py --manuscript 'thesis-typst/src/**/*.typ' \
      --references docs/references --extract-dir /tmp/paper-extracts-raw
"""

import argparse
import glob
import html
import os
import subprocess
import sys

STOP = set(
    "the a an of to in on for and or is are was were be by with as at from that this it "
    "its their than up over under into for we our can may".split()
)

FLAG_N = 8
REVIEW_N = 6
WINNOW_K = 5
WINNOW_W = 4  # guarantees detection of shared runs >= k + w - 1 = 8
JACCARD_THRESHOLD = 0.6


def normalize_tokens(raw: str) -> list[str]:
    text = html.unescape(raw)
    text = "".join(c if (c.isalnum() or c in "%- ") else " " for c in text)
    tokens = []
    for word in text.lower().split():
        word = word.strip(".,")
        if word and word not in STOP:
            tokens.append(word)
    return tokens


def manuscript_tokens(text: str) -> list[str]:
    import re

    text = re.sub(r"//[^\n]*", " ", text)
    text = re.sub(r"#[A-Za-z-]+(\([^)]*\))?", " ", text)
    text = re.sub(r"\$[^$]*\$", " ", text)
    text = re.sub(r"@[A-Za-z0-9_:-]+", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[\[\]{}()]", " ", text)
    return normalize_tokens(text)


def manuscript_sentences(text: str) -> list[str]:
    import re

    text = re.sub(r"//[^\n]*", " ", text)
    text = re.sub(r"\$[^$]*\$", " ", text)
    text = re.sub(r"@[A-Za-z0-9_:-]+", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[\[\]{}()]|#[A-Za-z-]+", " ", text)
    sentences = re.split(r"[.!?]+", text)
    return [s.strip() for s in sentences if len(s.split()) >= 8]


def extract_references(ref_dir: str, extract_dir: str) -> dict[str, str]:
    os.makedirs(extract_dir, exist_ok=True)
    extracts = {}
    for pdf in sorted(glob.glob(os.path.join(ref_dir, "*.pdf"))):
        stem = os.path.splitext(os.path.basename(pdf))[0]
        out = os.path.join(extract_dir, f"{stem}.md")
        with open(pdf, "rb") as fh:
            if fh.read(4) != b"%PDF":
                print(f"  skip broken: {stem}")
                continue
        if not os.path.exists(out):
            subprocess.run(["pdftotext", "-raw", pdf, out], check=True, capture_output=True)
        extracts[stem] = open(out, errors="ignore").read()
    return extracts


def maximal_overlaps(a: list[str], b: list[str], min_n: int) -> list[tuple[int, str]]:
    pos: dict[tuple, list[int]] = {}
    for i in range(len(b) - min_n + 1):
        pos.setdefault(tuple(b[i : i + min_n]), []).append(i)
    hits: list[tuple[int, str]] = []
    seen: set[tuple] = set()
    i = 0
    while i < len(a) - min_n + 1:
        key = tuple(a[i : i + min_n])
        if key in pos:
            best = 0
            for j in pos[key]:
                n = min_n
                while i + n < len(a) and j + n < len(b) and a[i + n] == b[j + n]:
                    n += 1
                best = max(best, n)
            if best >= min_n:
                span = tuple(a[i : i + best])
                if span not in seen:
                    seen.add(span)
                    hits.append((best, " ".join(span)))
                i += best
                continue
        i += 1
    return sorted(hits, reverse=True)


def winnow_fingerprints(tokens: list[str], k: int = WINNOW_K, w: int = WINNOW_W) -> set[int]:
    hashes = [hash(tuple(tokens[i : i + k])) for i in range(len(tokens) - k + 1)]
    if not hashes:
        return set()
    fps: set[int] = set()
    right = 0
    min_idx = -1
    while right < len(hashes):
        if right - min_idx >= w:
            min_idx = max(range(right - w + 1, right + 1), key=lambda x: -hashes[x])
            fps.add(hashes[min_idx])
        elif hashes[right] < hashes[min_idx]:
            min_idx = right
            fps.add(hashes[min_idx])
        right += 1
    return fps


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


AI_TELLS: dict[str, str] = {
    "delve": r"\bdelve",
    "crucial": r"\bcrucial",
    "moreover": r"\bmoreover\b",
    "furthermore": r"\bfurthermore\b",
    "notably": r"\bnotably\b",
    "it is worth noting": r"\bit is worth noting",
    "leverage": r"\bleverag",
    "seamless": r"\bseamless",
    "robust": r"\brobust",
    "landscape": r"\blandscape",
    "tapestry": r"\btapestry",
    "myriad": r"\bmyriad",
    "plethora": r"\bplethora",
    "harness": r"\bharness",
    "pivotal": r"\bpivotal",
    "foster": r"\bfoster",
    "underscore": r"\bunderscore",
    "not only but also": r"\bnot only\b[^.]*\bbut also\b",
    "in conclusion": r"\bin conclusion\b",
    "overall-comma": r"\boverall,",
}


def stylometric_report(text: str) -> list[str]:
    """T5: AI-tell scan. Signals only, never a verdict: peer-reviewed evaluations
    (Weber-Wulff et al. 2023; Liang et al. 2023) show AI detectors are unreliable
    and false-flag non-native English writing. This tier reports surface tells and
    burstiness so an author can remove them; it does not classify authorship."""
    import re

    prose = re.sub(r"//[^\n]*", " ", text)
    prose = re.sub(r"\$[^$]*\$", " ", prose)
    prose = re.sub(r"@[A-Za-z0-9_:-]+", " ", prose)
    findings = []
    for name, pat in AI_TELLS.items():
        n = len(re.findall(pat, prose, re.I))
        if n:
            findings.append(f"[T5-AI-TELL] {name}: {n}")
    em = prose.count("\u2014")
    if em:
        findings.append(f"[T5-AI-TELL] em-dash in prose: {em}")
    sentences = [s for s in re.split(r"[.]+", prose) if len(s.split()) >= 3]
    lengths = [len(s.split()) for s in sentences]
    mean = sum(lengths) / max(len(lengths), 1)
    var = sum((n_words - mean) ** 2 for n_words in lengths) / max(len(lengths), 1)
    print(
        f"T5 stats: {len(sentences)} sentences, mean {mean:.1f}w, "
        f"burstiness {var**0.5 / mean:.2f} (low uniformity is human-like)"
    )
    return findings


def audit(manuscript_glob: str, ref_dir: str, extract_dir: str) -> int:
    files = sorted(glob.glob(manuscript_glob, recursive=True))
    if not files:
        print(f"no manuscript files match {manuscript_glob}")
        return 2
    text = "\n".join(open(f).read() for f in files)
    mt = manuscript_tokens(text)
    msents = manuscript_sentences(text)
    print(f"manuscript: {len(files)} files, {len(mt)} content words, {len(msents)} sentences")

    extracts = extract_references(ref_dir, extract_dir)
    print(f"references: {len(extracts)} papers\n")

    findings = 0
    for stem, raw in extracts.items():
        rt = normalize_tokens(raw)
        rsents = [normalize_tokens(s) for s in raw.split(".") if len(s.split()) >= 8]

        for min_n, label in ((FLAG_N, "T1-FLAG"), (REVIEW_N, "T1-REVIEW")):
            for n, span in maximal_overlaps(mt, rt, min_n):
                findings += 1
                print(f"[{label}] {stem} ({n}w): {span[:150]}")

        mf, rf = winnow_fingerprints(mt), winnow_fingerprints(rt)
        shared = len(mf & rf)
        density = shared / max(len(mf), 1)
        if density > 0.01:
            findings += 1
            print(f"[T2-WINNOW] {stem}: {shared} shared fingerprints (density {density:.3f})")

        rsets = [set(s) for s in rsents if s]
        for sent in msents:
            mset = set(manuscript_tokens(sent))
            if len(mset) < 6:
                continue
            best = max((jaccard(mset, r) for r in rsets), default=0.0)
            if best >= JACCARD_THRESHOLD:
                findings += 1
                print(f"[T3-JACCARD {best:.2f}] {stem}: {sent[:140]}")

    try:
        from sentence_transformers import SentenceTransformer, util  # type: ignore

        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        memb = model.encode([s for s in msents], normalize_embeddings=True)
        for stem, raw in extracts.items():
            rsents = [s for s in raw.split(".") if len(s.split()) >= 8][:20000]
            remb = model.encode(rsents, normalize_embeddings=True)
            sims = util.cos_sim(memb, remb)
            for i in range(sims.shape[0]):
                j = int(sims[i].argmax())
                if float(sims[i, j]) >= 0.85:
                    findings += 1
                    print(f"[T4-SEMANTIC {float(sims[i, j]):.2f}] {stem}: {msents[i][:130]}")
        print("T4: embeddings active")
    except ImportError:
        print("T4: sentence-transformers not installed, tier skipped")

    for line in stylometric_report(text):
        findings += 1
        print(line)
    print(f"\nfindings: {findings}")
    return 0 if findings == 0 else 1


def self_test(ref_dir: str, extract_dir: str) -> int:
    extracts = extract_references(ref_dir, extract_dir)
    stem = next(s for s in extracts if "aapa" in s)
    rt = normalize_tokens(extracts[stem])
    verbatim = (
        "AAPA reduces SLO violations by up to 50% and lowers latency by 40% compared to "
        "Kubernetes HPA, albeit at 2-8x higher resource usage under spike-dominated conditions"
    )
    reordered = (
        "Albeit at higher resource usage under spike-dominated conditions, Kubernetes HPA "
        "is compared: AAPA lowers latency 40%, reduces SLO violations up to 50%, at 2-8x usage"
    )
    clean = (
        "The hybrid controller shifts traffic between two independent platforms and gates "
        "every proactive replica decision on a forecast confidence score."
    )
    vt, ot, ct = manuscript_tokens(verbatim), manuscript_tokens(reordered), manuscript_tokens(clean)
    t1 = maximal_overlaps(vt, rt, REVIEW_N)
    fp_v = winnow_fingerprints(vt) & winnow_fingerprints(rt)
    fp_o = winnow_fingerprints(ot) & winnow_fingerprints(rt)
    fp_c = winnow_fingerprints(ct) & winnow_fingerprints(rt)
    t2v = len(fp_v) / max(len(winnow_fingerprints(vt)), 1)
    t2c = len(fp_c) / max(len(winnow_fingerprints(ct)), 1)
    t2o = len(fp_o) / max(len(winnow_fingerprints(ot)), 1)

    rsents = [set(normalize_tokens(s)) for s in extracts[stem].split(".") if len(s.split()) >= 8]
    omax = max((jaccard(set(ot), r) for r in rsents), default=0.0)
    cmax = max((jaccard(set(ct), r) for r in rsents), default=0.0)

    ok = t1 and t2v > 0.1 and omax >= JACCARD_THRESHOLD and t2c < 0.05 and cmax < 0.3
    print(
        f"self-test: T1 verbatim {'PASS' if t1 else 'FAIL'} ({t1[0][0] if t1 else 0}w) | "
        f"T2 verbatim {t2v:.2f} {'PASS' if t2v > 0.1 else 'FAIL'} | "
        f"T3 reordered {omax:.2f} {'PASS' if omax >= JACCARD_THRESHOLD else 'FAIL'} | "
        f"T2/T3 clean-control {t2c:.2f}/{cmax:.2f} "
        f"{'PASS' if t2c < 0.05 and cmax < 0.3 else 'FAIL'}"
    )
    print(f"(info) T2 on reordered plant: {t2o:.2f} — winnowing is not expected to fire here")
    return 0 if ok else 3


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manuscript", default="thesis-typst/src/**/*.typ")
    ap.add_argument("--references", default="docs/references")
    ap.add_argument("--extract-dir", default="/tmp/paper-extracts-raw")
    ap.add_argument("--self-test-only", action="store_true")
    args = ap.parse_args()
    rc = self_test(args.references, args.extract_dir)
    if rc or args.self_test_only:
        return rc
    print()
    return audit(args.manuscript, args.references, args.extract_dir)


if __name__ == "__main__":
    sys.exit(main())
