import html
import pathlib
import re

import pytest

MTG = pytest.importorskip("openalea.mtg").MTG

import openalea.widgets.mtg as oa_mtg  # noqa: E402
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


def test_mtg_with_several_plants(monkeypatch):
    # issue #12: the vertices of the plants after the first one had no level
    g = MTG()
    for _ in range(2):
        plant = g.add_component(g.root, label="P")
        base = g.add_component(plant, label="I")
        g.add_child(base, label="I", edge_type="<")
        g.add_child(base, label="I", edge_type="+")
    added = {}
    add_node = oa_mtg.Network.add_node
    monkeypatch.setattr(oa_mtg.Network, "add_node",
                        lambda self, vid, **kw: (added.__setitem__(vid, kw), add_node(self, vid, **kw))[1])
    plot(g)
    assert sorted(added) == sorted(g.vertices(scale=2))
    for plant in g.vertices(scale=1):
        base, *others = g.components(plant)
        assert added[base]["level"] == 0 and added[base]["shape"] == "box"
        assert all(added[vid]["level"] == 1 for vid in others)
    # each plant has its own color
    colors = {added[next(iter(g.components(plant)))]["color"] for plant in g.vertices(scale=1)}
    assert len(colors) == 2
