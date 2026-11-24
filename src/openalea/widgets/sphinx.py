"""Sphinx extension for documentations with notebooks using OpenAlea widgets.

Add it to the extensions of the conf.py of the documentation::

    extensions = [..., "openalea.widgets.sphinx"]

It loads nbsphinx, and makes the kernels that nbsphinx starts to execute the
notebooks display k3d plots (PlantGL, MTG, lpy magic, k3d) as snapshots, which
show in the static pages of the documentation (see openalea.widgets.display).
Notebooks are only executed by nbsphinx when they are saved without outputs.
"""
from .version import __version__

# run by the kernel when it starts (IPython exec_lines)
_KERNEL_SETUP = "from openalea.widgets.display import use_snapshots; use_snapshots()"


def _add_kernel_setup(app, config):
    arguments = list(config.nbsphinx_execute_arguments or [])
    arguments.append(f"--IPKernelApp.exec_lines={_KERNEL_SETUP}")
    config.nbsphinx_execute_arguments = arguments


def setup(app):
    app.setup_extension("nbsphinx")
    app.connect("config-inited", _add_kernel_setup)
    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
