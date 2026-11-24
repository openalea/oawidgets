"""Display k3d plots as snapshots, for static pages.

k3d 3 widgets are anywidgets, which static pages (documentation built with
nbsphinx, notebooks saved with their outputs) cannot load: their 3D views stay
empty. A k3d snapshot shows everywhere: an interactive 3D view (rotate, zoom,
k3d panel) embedded in the cell output as HTML. It loads the k3d viewer from
unpkg, so it needs an internet connection.

In notebooks, PlantGL, MTG and k3d plots are k3d widgets, as usual. For a static
page:

- show_plot(plot) displays one plot as a snapshot;
- use_snapshots() makes the notebook display every k3d plot as a snapshot: the
  plots that are the result of a cell, passed to IPython display or shown with
  plot.display(). The Sphinx extension openalea.widgets.sphinx calls it in the
  kernels that nbsphinx starts to execute the notebooks of a documentation.
"""
import html
import importlib

from IPython.display import HTML, display

# k3d Plot.display, saved while use_snapshots replaces it
_widget_display = None


def _plot_class():
    # k3d.plot is the plot function; the class is in the module of the same name
    return importlib.import_module("k3d.plot").Plot


def iframe(page, attributes=""):
    """An HTML output showing a whole HTML page, embedded in an iframe (srcdoc).

    The iframe keeps the scripts of the page apart from the notebook or the
    documentation page. Besides the HTML special characters, the control and
    non-ASCII characters of the page are written as character references: some
    of them are line breaks for docutils (U+2028, U+2029, U+0085, form feed...
    in inlined scripts, such as vis-network for pyvis), which would end the raw
    HTML of the output in a documentation built with nbsphinx.

    The C1 controls (U+0080-U+009F) have no character reference (browsers read
    them as windows-1252 characters): they are written as JavaScript escapes
    (\\u0085), the same characters in the string literals of scripts, where
    they are found (they have no use in HTML text).

    Parameters
    ----------
    page : str
        The HTML page.
    attributes : str, optional
        More attributes of the iframe, such as 'style="border: none"'.
    """
    srcdoc = "".join(
        c if " " <= c <= "~" or c in "\n\t"
        else f"\\u{ord(c):04x}" if "\x80" <= c <= "\x9f"
        else f"&#x{ord(c):x};"
        for c in html.escape(page)
    )
    # the div avoids the IPython warning about HTML starting with an iframe
    return HTML(f'<div><iframe srcdoc="{srcdoc}" {attributes}></iframe></div>')


def show_plot(plot, live=False):
    """Display a k3d plot in the notebook.

    Parameters
    ----------
    plot : k3d plot
        For instance the plot returned by PlantGL.
    live : bool, optional
        If False (default), display a snapshot of the plot: an interactive 3D
        view that also shows in static pages. If True, display the k3d widget,
        which stays connected to Python (for instance to change the plot after
        displaying it), even when use_snapshots is on.
    """
    if live:
        (_widget_display or type(plot).display)(plot)
        return
    plot.snapshot_type = "online"
    page = plot.get_snapshot()
    display(iframe(page, f'style="width: 100%; height: {plot.height}px; border: none"'))


def use_snapshots(enable=True):
    """Display every k3d plot as a snapshot (see show_plot), or as a widget again.

    It applies to the plots that are the result of a cell, passed to IPython
    display, or shown with plot.display(), in the current Python process (the
    notebook kernel). Plots are still k3d plots: objects can be added to them.

    Parameters
    ----------
    enable : bool, optional
        True (default) to display plots as snapshots, False to display them as
        k3d widgets again.
    """
    global _widget_display
    plot_class = _plot_class()
    if enable and _widget_display is None:
        _widget_display = plot_class.display
        # IPython calls _ipython_display_ instead of showing the widget;
        # k3d display() would show the widget inside an Output widget
        plot_class._ipython_display_ = lambda self: show_plot(self)
        plot_class.display = lambda self, **kwargs: show_plot(self)
    elif not enable and _widget_display is not None:
        del plot_class._ipython_display_
        plot_class.display = _widget_display
        _widget_display = None
