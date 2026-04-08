from __future__ import annotations

from app.models import BBox, Block, Confidence, Table, TableCell
from app.semantic.mcq_extractor import build_question_bank, extract_mcqs_from_table


def test_extract_bn_mcq_from_text() -> None:
    text = """
1. বাংলাদেশের রাজধানী কোথায়?
ক) ঢাকা
খ) চট্টগ্রাম
গ) সিলেট
ঘ) রাজশাহী
উত্তর: ক
""".strip()
    blocks = [
        Block(
            block_id="b_0000_0000",
            page_index=0,
            type="paragraph",
            bbox=BBox(x0=0, y0=0, x1=1, y1=1),
            reading_order=0,
            text=text,
            spans=[],
            confidence=Confidence(score=1.0, method="native_pdf_text", signals={}),
        )
    ]
    qs = build_question_bank(blocks, [])
    assert len(qs) >= 1
    q0 = qs[0]
    assert "রাজধানী" in q0.stem or "বাংলাদেশ" in q0.stem
    assert len(q0.options) >= 2
    assert q0.correct_option_label in ("ক", "K", None) or q0.correct_option_label == "ক"


def test_table_grid_mcq() -> None:
    cells = [
        TableCell(row=0, col=0, text="প্রশ্ন"),
        TableCell(row=0, col=1, text="ক"),
        TableCell(row=0, col=2, text="খ"),
        TableCell(row=0, col=3, text="গ"),
        TableCell(row=0, col=4, text="ঘ"),
        TableCell(row=1, col=0, text="২+২ কত?"),
        TableCell(row=1, col=1, text="৩"),
        TableCell(row=1, col=2, text="৪"),
        TableCell(row=1, col=3, text="৫"),
        TableCell(row=1, col=4, text="৬"),
    ]
    t = Table(
        table_id="t_test",
        page_index=0,
        bbox=BBox(x0=0, y0=0, x1=100, y1=100),
        n_rows=2,
        n_cols=5,
        cells=cells,
        csv_path="tables/x.csv",
        method="test",
        confidence=Confidence(score=0.9, method="test", signals={}),
    )
    qs = extract_mcqs_from_table(t)
    assert len(qs) >= 1
    assert qs[0].stem
