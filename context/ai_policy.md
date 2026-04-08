## AI policy

This engine provides **structured extraction + confidence scoring**. Any downstream LLM usage (e.g., generating quizzes) should:
- Consume canonical outputs (JSON + confidence)
- Use **low-confidence** areas to request human review or apply conservative transformations
- Avoid hallucinating missing content; only transform/explain extracted text

