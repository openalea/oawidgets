import html
import pathlib
import re

import pytest

MTG = pytest.importorskip("openalea.mtg").MTG

from openalea.widgets.mtg import plot  # noqa: E402

data = pathlib.Path(__file__).parent.resolve() / "data"


def test_mtg(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    g = MTG(data / "boutdenoylum2.mtg")
    output = plot(g)
    # the network page is embedded in the output, with its scripts
    match = re.fullmatch(r'<div><iframe srcdoc="(.*)" width="[^"]*" height="[^"]*" style="[^"]*"></iframe></div>',
                         output.data, re.S)
    assert match is not None
    page = html.unescape(match.group(1))
    assert "vis.Network" in page or "vis-network" in page
    # vis-network has line separators (U+2028...), escaped for nbsphinx
    assert output.data.isascii()
    assert len(output.data.splitlines()) == output.data.count("\n") + 1
    # no file written next to the notebook
    assert list(tmp_path.iterdir()) == []
