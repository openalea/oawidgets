import html
import re

import k3d
import numpy as np
import pytest
from IPython.core.formatters import DisplayFormatter

import openalea.widgets.display as oa_display
from openalea.widgets.display import show_plot, snapshot_display


@pytest.fixture
def displayed(monkeypatch):
    """The objects passed to IPython display by show_plot."""
    objects = []
    monkeypatch.setattr(oa_display, "display", objects.append)
    return objects


def _plot():
    plot = k3d.plot()
    plot += k3d.points(np.zeros((1, 3), dtype=np.float32), point_size=1.0)
    return plot


def _snapshot_page(output):
    """The snapshot page in the iframe of an HTML output."""
    match = re.fullmatch(
        r'<div><iframe srcdoc="(.*)" style="[^"]*"></iframe></div>', output.data, re.S
    )
    assert match is not None
    return html.unescape(match.group(1))


def test_show_plot_displays_an_online_snapshot(displayed):
    show_plot(_plot())
    assert len(displayed) == 1
    page = _snapshot_page(displayed[0])
    assert page.startswith("<!doctype html>")
    # the k3d viewer of the installed version, loaded from unpkg
    assert f"https://unpkg.com/k3d@{k3d.__version__}/dist/standalone.js" in page


def test_show_plot_live_displays_the_widget(monkeypatch, displayed):
    plot = snapshot_display(_plot())
    shown = []
    monkeypatch.setattr(type(plot), "display", lambda self: shown.append(self))
    show_plot(plot, live=True)
    assert shown == [plot] and displayed == []
    # displayed as a widget from now on
    assert "_ipython_display_" not in plot.__dict__


def test_snapshot_display_as_cell_result(displayed):
    plot = snapshot_display(_plot())
    # what the notebook does with the result of a cell
    data, _ = DisplayFormatter().format(plot)
    assert data == {}
    assert len(displayed) == 1
    _snapshot_page(displayed[0])
    # objects can still be added, and other plots are widgets as before
    plot += k3d.points(np.ones((1, 3), dtype=np.float32), point_size=1.0)
    other, _ = DisplayFormatter().format(k3d.plot())
    assert "application/vnd.jupyter.widget-view+json" in other
