import importlib.util
from pathlib import Path

import pytest


@pytest.mark.parametrize("script,report", [
    ("review_social_next80_20261109.py", "social-next80-quality-review-20261109.json"),
    ("review_social_fixed95_20261109.py", "social-fixed95-quality-review-20261109.json"),
    ("review_app_next240_quality_20261109.py", "app-next240-quality-review-20261109.json"),
])
def test_completed_fixed_batch_cannot_reset_later_reviews(tmp_path, script, report):
    path = Path(__file__).parents[1] / "research/audit" / script
    spec = importlib.util.spec_from_file_location("fixed_review", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = tmp_path
    target = tmp_path / "data/reviews" / report
    target.parent.mkdir(parents=True)
    target.write_text('{"preserved":true}', encoding="utf-8")
    with pytest.raises(SystemExit, match="already"):
        module.main()
    assert target.read_text(encoding="utf-8") == '{"preserved":true}'
    assert not (tmp_path / "data/research.sqlite3").exists()
