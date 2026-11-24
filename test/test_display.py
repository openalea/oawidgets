import html
import re
from types import SimpleNamespace

import k3d
import numpy as np
import pytest
from IPython.core.formatters import DisplayFormatter

import openalea.widgets.display as oa_display
import openalea.widgets.sphinx as oa_sphinx
from openalea.widgets.display import show_plot, use_snapshots

WIDGET = "application/vnd.jupyter.widget-view+json"


@pytest.fixture
def displayed(monkeypatch):
    """The objects passed to IPython display by show_plot."""
    objects = []
    monkeypatch.setattr(oa_display, "display", objects.append)
    return objects


@pytest.fixture
def snapshots():
    """use_snapshots on during the test, off afterwards."""
    use_snapshots()
    yield
    use_snapshots(False)


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


def test_plots_are_widgets_by_default():
    data, _ = DisplayFormatter().format(_plot())
    assert WIDGET in data


def test_use_snapshots_for_cell_results(displayed, snapshots):
    plot = _plot()
    # what the notebook does with the result of a cell
    data, _ = DisplayFormatter().format(plot)
    assert data == {}
    assert len(displayed) == 1
    _snapshot_page(displayed[0])
    # objects can still be added
    plot += k3d.points(np.ones((1, 3), dtype=np.float32), point_size=1.0)


def test_use_snapshots_for_plot_display(displayed, snapshots):
    # k3d's own idiom would otherwise show the widget in an Output widget
    _plot().display()
    assert len(displayed) == 1
    _snapshot_page(displayed[0])


def test_show_plot_live_is_the_k3d_widget_display(monkeypatch, displayed):
    shown = []
    # the class use_snapshots changes (plots are instances of a subclass of it)
    monkeypatch.setattr(oa_display._plot_class(), "display", lambda self, **kw: shown.append(self))
    use_snapshots()
    try:
        plot = _plot()
        show_plot(plot, live=True)
    finally:
        use_snapshots(False)
    assert shown == [plot] and displayed == []


def test_use_snapshots_off_restores_widgets(displayed):
    use_snapshots()
    use_snapshots()  # twice: no effect
    use_snapshots(False)
    data, _ = DisplayFormatter().format(_plot())
    assert WIDGET in data
    assert displayed == []


def test_sphinx_extension_sets_up_the_kernels():
    config = SimpleNamespace(nbsphinx_execute_arguments=["--InlineBackend.figure_formats={'svg'}"])
    oa_sphinx._add_kernel_setup(None, config)
    assert config.nbsphinx_execute_arguments == [
        "--InlineBackend.figure_formats={'svg'}",
        "--IPKernelApp.exec_lines=from openalea.widgets.display import use_snapshots; use_snapshots()",
    ]
