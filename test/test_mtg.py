import pytest

MTG = pytest.importorskip("openalea.mtg").MTG

from openalea.widgets.mtg import plot  # noqa: E402
import pathlib

data = pathlib.Path(__file__).parent.resolve() / "data"


def test_mtg():
    g = MTG(data / "boutdenoylum2.mtg")
    plot(g)
