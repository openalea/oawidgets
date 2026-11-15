"""Display k3d plots in notebooks, also in static pages.

k3d 3 widgets are anywidgets, which static pages (the documentation built with
nbsphinx, notebooks saved with their outputs) cannot load: their 3D views stay
empty. A k3d snapshot shows everywhere: an interactive 3D view (rotate, zoom,
k3d panel) embedded in the cell output as HTML. It loads the k3d viewer from
unpkg, so it needs an internet connection.

PlantGL and MTG return plots marked with snapshot_display: the notebook shows
them as snapshots, when they are the result of a cell or passed to IPython
display. show_plot(plot, live=True) shows the k3d widget instead.
"""
import html

from IPython.display import HTML, display


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
        displaying it); the plot is then displayed as a widget from now on.
    """
    if live:
        # back to the k3d widget display (see snapshot_display)
        plot.__dict__.pop("_ipython_display_", None)
        plot.display()
        return
    plot.snapshot_type = "online"
    page = plot.get_snapshot()
    # the iframe keeps the scripts of the snapshot apart from the page; the div
    # avoids the IPython warning about HTML starting with an iframe
    display(
        HTML(
            f'<div><iframe srcdoc="{html.escape(page)}" '
            f'style="width: 100%; height: {plot.height}px; border: none"></iframe></div>'
        )
    )


def snapshot_display(plot):
    """Make the notebook display plot as a snapshot (see show_plot).

    It applies when plot is the result of a cell, or is passed to IPython
    display. Other plots are not affected. The plot is still a k3d plot:
    objects can be added to it.

    Returns
    -------
    plot : the same plot
    """
    # IPython calls _ipython_display_ instead of showing the widget
    plot._ipython_display_ = lambda: show_plot(plot)
    return plot
