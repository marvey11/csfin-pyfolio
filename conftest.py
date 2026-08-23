from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def mock_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect home/config paths to a isolated temp directory for all tests."""
    config_dir = tmp_path / ".codescape" / "pyfolio"
    config_dir.mkdir(parents=True)
    monkeypatch.setenv("PYFOLIO_CONFIG_DIR", str(config_dir))
    return config_dir
