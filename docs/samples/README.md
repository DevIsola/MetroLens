# Discovery-only source observations

`official-page-observations.csv` contains five manually transcribed, attributed observations from official publisher HTML pages (reviewed 2026-10-26). It is **not** a downloaded Statistics Canada CSV, CMHC Excel workbook, or Bank of Canada Valet response. It must never be used by the production frontend or gold data marts. See [`../SOURCE_VALIDATION_M00_T02.md`](../SOURCE_VALIDATION_M00_T02.md) for provenance, licensing, semantics and outstanding verification work.

Run `python scripts/validate_source_samples.py` from the repository root to validate this fixture and `python -m unittest discover -s tests -v` for negative comparability tests.
