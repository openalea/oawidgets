# widgets

[![Docs](https://readthedocs.org/projects/oawidgets/badge/?version=latest)](https://oawidgets.readthedocs.io/)
[![Build Status](https://github.com/openalea/oawidgets/actions/workflows/openalea_ci.yml/badge.svg)](https://github.com/openalea/oawidgets/actions/workflows/openalea_ci.yml?query=branch%3Amaster)
[![Python Version](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License--CeCILL-C-blue)](https://www.cecill.info/licences/Licence_CeCILL-C_V1-en.html)
[![Anaconda-Server Badge](https://anaconda.org/openalea3/openalea.widgets/badges/version.svg)](https://anaconda.org/openalea3/openalea.widgets)


widgets is a set of OpenAlea widgets for jupyter notebooks allowing to: 
- use a magic to use [LPy](https://lpy.readthedocs.io) language
- display interactive 3D plant architectures, using [openalea.plantgl](https://github.com/openalea/plantgl)
- display [MTG](https://mtg.readthedocs.io) to explore for instance class and number of vertices, number of scales, properties, using [Pyvis](https://pyvis.readthedocs.io)
- show these 3D views, and any [k3d](https://k3d-jupyter.org) plot, in static pages such as a documentation built with nbsphinx, through a Sphinx extension (see [below](#notebooks-in-a-documentation-static-pages))


### Authors

> - Baptiste Brument
> - Christophe Pradal

## Installation

```bash
mamba install -c openalea3 -c conda-forge openalea.widgets
```

If you want to use the lpy extension, install also lpy

```bash
mamba install -c openalea3 -c conda-forge openalea.widgets openalea.lpy
```

### Usage :

See documentation and notebook examples on [https://oawidgets.readthedocs.io](https://oawidgets.readthedocs.io).

### Notebooks in a documentation (static pages)

The 3D views (PlantGL, MTG, lpy magic, and any k3d plot) are k3d widgets: they stay
empty in static pages, such as a documentation built with nbsphinx or a notebook saved
with its outputs. They show there as snapshots: interactive 3D views (rotate, zoom)
embedded in the page, which need an internet connection to load the k3d viewer.

**Documentation built with nbsphinx (recommended).** Add the Sphinx extension of
openalea.widgets to the `conf.py` of the documentation, nothing else to do:

```python
extensions = [..., "openalea.widgets.sphinx"]
```

It loads nbsphinx and, in the notebooks nbsphinx executes, displays every k3d plot as a
snapshot, whether it comes from openalea.widgets or from k3d directly (`plot`,
`plot.display()`, `display(plot)`). The notebooks need no change and stay live in
Jupyter. nbsphinx only executes the notebooks saved without outputs: clear them before
committing.

**Without the extension** (static page made otherwise, notebook shared with its outputs),
the snapshots are up to you, in the notebook itself:

```python
from openalea.widgets.display import show_plot, use_snapshots

show_plot(plot)   # this plot as a snapshot
use_snapshots()   # every k3d plot displayed from now on, as with the extension
```

`show_plot(plot, live=True)` still displays the live widget.

### License

Our code is released under [Cecill-C](https://cecill.info/licences/Licence_CeCILL_V1.1-US.txt) licence. (see LICENSE file for details).

## Contributors

<a href="https://github.com/openalea/oawidgets/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=openalea/oawidgets" />
</a>