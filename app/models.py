from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class BBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float


class Confidence(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    method: str
    signals: dict[str, Any] = Field(default_factory=dict)


BlockType = Literal[
    "heading",
    "paragraph",
    "list_item",
    "question",
    "answer",
    "footer",
    "header",
    "table",
    "figure",
    "equation",
    "unknown",
]


class TextSpan(BaseModel):
    text: str
    bbox: BBox
    lang: str | None = None
    confidence: Confidence


class Block(BaseModel):
    block_id: str
    page_index: int = Field(ge=0)
    type: BlockType
    bbox: BBox
    reading_order: int = Field(ge=0)
    column_index: int | None = Field(default=None, ge=0)
    text: str
    spans: list[TextSpan] = Field(default_factory=list)
    derived: dict[str, Any] = Field(default_factory=dict)
    confidence: Confidence


class Page(BaseModel):
    page_index: int = Field(ge=0)
    width_px: int = Field(ge=1)
    height_px: int = Field(ge=1)
    image_path: str
    thumbnail_path: str | None = None


class TableCell(BaseModel):
    row: int = Field(ge=0)
    col: int = Field(ge=0)
    rowspan: int = Field(default=1, ge=1)
    colspan: int = Field(default=1, ge=1)
    text: str


class Table(BaseModel):
    table_id: str
    page_index: int = Field(ge=0)
    bbox: BBox
    n_rows: int = Field(ge=0)
    n_cols: int = Field(ge=0)
    cells: list[TableCell]
    csv_path: str
    method: str | None = None
    confidence: Confidence


class ExtractedImage(BaseModel):
    image_id: str
    page_index: int = Field(ge=0)
    bbox: BBox
    path: str
    caption_block_id: str | None = None
    confidence: Confidence


class Source(BaseModel):
    input_path: str
    file_type: Literal["pdf"] = "pdf"
    sha256: str | None = None


class Metadata(BaseModel):
    created_at: str
    page_count: int = Field(ge=1)
    title: str | None = None
    authors: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=lambda: ["ben", "eng"])


class Exports(BaseModel):
    json_path: str
    markdown_path: str
    html_path: str
    tables_dir: str | None = None
    images_dir: str | None = None


class ConfidenceSummary(BaseModel):
    overall: Confidence
    components: dict[str, Confidence]
    notes: list[str] = Field(default_factory=list)


class CanonicalDocument(BaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    source: Source
    metadata: Metadata
    pages: list[Page]
    blocks: list[Block]
    tables: list[Table] = Field(default_factory=list)
    images: list[ExtractedImage] = Field(default_factory=list)
    exports: Exports
    confidence: ConfidenceSummary

