import html
import pathlib
import re

from openalea.mtg import MTG
from openalea.widgets.mtg import plot

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
    # no file written next to the notebook
    assert list(tmp_path.iterdir()) == []
