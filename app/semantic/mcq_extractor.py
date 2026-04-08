from __future__ import annotations

import re
from typing import Iterable

from app.models import Block, Confidence, McqOption, McqQuestion, Table


def _norm_line(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _mcq_confidence(
    n_opts: int,
    has_answer: bool,
    stem_len: int,
) -> Confidence:
    score = 0.62
    if n_opts >= 4:
        score += 0.18
    elif n_opts >= 2:
        score += 0.08
    if has_answer:
        score += 0.14
    if stem_len >= 12:
        score += 0.06
    score = max(0.0, min(1.0, score))
    return Confidence(
        score=score,
        method="mcq_heuristic_v1",
        signals={"n_options": n_opts, "has_declared_answer": has_answer, "stem_chars": stem_len},
    )


# Bengali MCQ labels (ক খ গ ঘ) — common textbook style
_RE_BN_OPT = re.compile(
    r"^\s*([কখগঘ])\s*[\).:]\s*(.+)$",
)
# English (A–D / a–d)
_RE_EN_OPT = re.compile(
    r"^\s*\(?\s*([A-Da-d])\s*\)?\s*[\).:]\s*(.+)$",
)
# Question line: "12." or "12)" or "১২."
_RE_Q_START = re.compile(
    r"^\s*(?:\(?(\d+)\)?[.)]|[\u09E6-\u09EF]+[.)])\s*(.*)$",
)
# Answer key lines
_RE_ANS_BN = re.compile(
    r"(?:উত্তর|সঠিক\s*উত্তর|উত্তরটি)\s*[:ঃ]?\s*([কখগঘ])",
    re.IGNORECASE,
)
_RE_ANS_EN = re.compile(
    r"(?:^|\s)(?:Ans(?:wer)?|Answer)\s*[:.]?\s*\(?\s*([A-Da-d])\s*\)?",
    re.IGNORECASE,
)
_RE_ANS_INLINE = re.compile(
    r"\(\s*([কখগঘA-Da-d])\s*\)\s*(?:সঠিক|correct|ok)?",
)


def _parse_options(lines: list[str]) -> tuple[list[McqOption], str | None]:
    opts: list[McqOption] = []
    answer_hint: str | None = None
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        am = _RE_ANS_BN.search(s) or _RE_ANS_EN.search(s)
        if am and not (_RE_BN_OPT.match(s) or _RE_EN_OPT.match(s)):
            answer_hint = am.group(1)
            if answer_hint and answer_hint.isalpha() and len(answer_hint) == 1:
                answer_hint = answer_hint.upper()
            continue
        m = _RE_BN_OPT.match(s)
        if m:
            opts.append(McqOption(label=m.group(1), text=_norm_line(m.group(2))))
            continue
        m = _RE_EN_OPT.match(s)
        if m:
            opts.append(McqOption(label=m.group(1).upper(), text=_norm_line(m.group(2))))
            continue
    return opts, answer_hint


def _extract_answer_from_tail(text: str) -> str | None:
    t = text.replace("\u09f7", ":")  # Bengali khanda ta sometimes used
    for pat in (_RE_ANS_BN, _RE_ANS_EN, _RE_ANS_INLINE):
        m = pat.search(t)
        if m:
            lab = m.group(1)
            return lab.upper() if lab.isalpha() and len(lab) == 1 else lab
    return None


def _parse_mcq_blocks(lines: list[str], page_index: int, base_id: str, block_ids: list[str]) -> list[McqQuestion]:
    out: list[McqQuestion] = []
    i = 0
    q_idx = 0
    n = len(lines)
    while i < n:
        stripped = lines[i].strip()
        if not stripped:
            i += 1
            continue
        m0 = _RE_Q_START.match(stripped)
        if not m0:
            i += 1
            continue
        stem_first = _norm_line(m0.group(2) or "")
        stem_parts: list[str] = ([stem_first] if stem_first else [])
        j = i + 1
        opt_lines: list[str] = []
        while j < n:
            s = lines[j].strip()
            if not s:
                j += 1
                continue
            if (_RE_BN_OPT.match(s) or _RE_EN_OPT.match(s)) or _RE_ANS_BN.search(s) or _RE_ANS_EN.search(s):
                opt_lines.append(lines[j])
                j += 1
                if _RE_ANS_BN.search(s) or _RE_ANS_EN.search(s):
                    break
                continue
            if _RE_Q_START.match(s) and opt_lines:
                break
            if not opt_lines:
                stem_parts.append(s)
                j += 1
                continue
            break
        stem = _norm_line("\n".join(stem_parts))
        full_tail = stem + "\n" + "\n".join(x.strip() for x in opt_lines)
        opts, ans_from_opts = _parse_options(opt_lines)
        ans = ans_from_opts or _extract_answer_from_tail(full_tail) or _extract_answer_from_tail(stem)
        if len(opts) >= 2 and len(stem) >= 2:
            q_idx += 1
            qid = f"q_{page_index:04d}_{q_idx:03d}_{base_id}"
            out.append(
                McqQuestion(
                    question_id=qid,
                    page_index=page_index,
                    stem=stem,
                    options=opts,
                    correct_option_label=ans,
                    correct_answer_text=None,
                    source="text",
                    source_table_id=None,
                    source_block_ids=list(block_ids),
                    confidence=_mcq_confidence(len(opts), ans is not None, len(stem)),
                )
            )
        i = j
    return out


def extract_mcqs_from_page_text(
    page_index: int,
    text: str,
    source_block_ids: list[str],
) -> list[McqQuestion]:
    lines = text.splitlines()
    return _parse_mcq_blocks(lines, page_index, "txt", source_block_ids)


def _row_cells_text(row: list[str]) -> list[str]:
    return [_norm_line(c) for c in row]


def extract_mcqs_from_table(table: Table) -> list[McqQuestion]:
    """
    If a table looks like a question grid (multiple columns with option-like headers or 4+ data columns),
    emit one McqQuestion per body row.
    """
    if table.n_rows < 2 or table.n_cols < 3:
        return []
    # Build matrix
    mat: list[list[str]] = [["" for _ in range(table.n_cols)] for _ in range(table.n_rows)]
    for c in table.cells:
        if c.row < table.n_rows and c.col < table.n_cols:
            mat[c.row][c.col] = c.text or ""

    header = [_norm_line(x) for x in mat[0]]
    header_joined = " ".join(header).lower()
    looks_mcq = table.n_cols >= 5 or any(
        x in header_joined
        for x in (
            "ক",
            "খ",
            "গ",
            "ঘ",
            "প্রশ্ন",
            "question",
            "option",
            "উত্তর",
            "ans",
        )
    )
    if not looks_mcq:
        return []

    out: list[McqQuestion] = []
    start_row = 1
    for r in range(start_row, table.n_rows):
        row = mat[r]
        if not any(row):
            continue
        stem = row[0] if row else ""
        opts: list[McqOption] = []
        labels_bn = ["ক", "খ", "গ", "ঘ"]
        labels_en = ["A", "B", "C", "D"]
        # Assume cols 1..4 are options when wide enough
        max_k = min(4, len(row) - 1)
        for k in range(max_k):
            lab = labels_bn[k] if k < len(labels_bn) else labels_en[k]
            cell = row[k + 1] if k + 1 < len(row) else ""
            if cell:
                opts.append(McqOption(label=lab, text=_norm_line(cell)))
        ans: str | None = None
        if len(row) > max_k + 1:
            tail = _norm_line(row[-1])
            ans = _extract_answer_from_tail(tail)
            if ans is None and tail:
                ans = tail[:1]
        if len(opts) >= 2 and len(stem) >= 3:
            out.append(
                McqQuestion(
                    question_id=f"q_tbl_{table.table_id}_{r:02d}",
                    page_index=table.page_index,
                    stem=stem,
                    options=opts,
                    correct_option_label=ans,
                    correct_answer_text=None,
                    source="table",
                    source_table_id=table.table_id,
                    source_block_ids=[],
                    confidence=_mcq_confidence(len(opts), ans is not None, len(stem)),
                )
            )
    return out


def build_question_bank(blocks: Iterable[Block], tables: Iterable[Table]) -> list[McqQuestion]:
    blocks_list = list(blocks)
    tables_list = list(tables)
    by_page: dict[int, list[Block]] = {}
    for b in sorted(blocks_list, key=lambda x: (x.page_index, x.reading_order)):
        by_page.setdefault(b.page_index, []).append(b)

    questions: list[McqQuestion] = []
    for pi, bs in sorted(by_page.items()):
        joined = "\n".join((b.text or "").strip() for b in bs if (b.text or "").strip())
        ids = [b.block_id for b in bs]
        questions.extend(extract_mcqs_from_page_text(pi, joined, ids))

    seen_ids = {q.question_id for q in questions}
    for t in tables_list:
        for q in extract_mcqs_from_table(t):
            if q.question_id not in seen_ids:
                questions.append(q)
                seen_ids.add(q.question_id)

    questions.sort(key=lambda q: (q.page_index, q.question_id))
    return questions
