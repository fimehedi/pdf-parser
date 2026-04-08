## Product brief

### Problem
Most textbooks and study books are distributed as **scanned PDFs** with:
- Mixed **Bengali + English** text
- Multi-column layouts
- Tables, diagrams, and figures
- Varying scan quality (skew, blur, noise)

These PDFs are hard to turn into structured educational content (questions, quizzes, lesson plans).

### Goal
Build a robust **scanned PDF processing engine** that:
- Converts scanned pages into structured blocks (text/table/figure)
- Reconstructs reading order and hierarchy
- Produces outputs for downstream educational tools
- Emits **confidence scores** to guide human review and quality control

### Primary users
- Content teams: build quizzes, flashcards, homework from PDFs
- Platform engineers: integrate outputs into learning workflows
- QA/reviewers: fix low-confidence OCR/layout/table segments

