from __future__ import absolute_import

try:
    from openalea.mtg import traversal
except ImportError as error:
    raise ImportError(
        "openalea.widgets.mtg displays MTGs, and needs openalea.mtg: "
        "mamba install -c openalea3 -c conda-forge openalea.mtg"
    ) from error
from pyvis.network import Network

from .display import iframe

try:
    import colorcet as cc
except ImportError:
    cc = None

def dict2html(args, properties=None):
    """Return a HTML element from a dictionary"""
    if properties is None:
        selection = ['index', 'parent', 'complex', 'label', 'edge_type', 'scale']
        properties =  []
        for k in args:
            if k not in selection:
                properties.append(k)
    elif isinstance(properties, str):
        properties = [properties]
    properties.sort()
    return '<br>'.join(['%s %s'%(k, args[k]) for k in properties])


def plot(g, properties=None, selection=None, hlayout=True, scale=None, labels=None, height='800px', width='900px', cdn_resources='in_line', **kwds):
    """Plot a MTG in the Jupyter Notebook"""
    G = Network(notebook=True, directed=True,
                layout=hlayout, heading="",
                height=height, width=width, 
                cdn_resources=cdn_resources)

    if hlayout:
        G.hrepulsion()
        G.options.layout.hierarchical.direction='DU'
        G.options.layout.hierarchical.parentCentralization=True
        G.options.layout.hierarchical.levelSeparation=150
    else:
    	G.repulsion()

    if scale is None:
        scale = g.max_scale()

    #Colors
    if cc is not None:
        colors = cc.glasbey_light
    else:
        colors = ['#6e6efd', '#fb7e81', '#ad85e4', '#7be141', '#ffff00', '#ffa807', '#eb7df4', '#e6ffe3', '#d2e5ff', '#ffd1d9']

    #Data
    vids = g.vertices(scale=scale)
    edges = [(g.parent(vid), vid, 6 if g.edge_type(vid) == '<' else 1)
             for vid in vids if g.parent(vid) is not None]

    # Roots of the trees at the scale (one per plant when the MTG has several
    # plants), and of the trees of their complexes
    roots = [vid for vid in vids if g.parent(vid) is None]
    complex_roots = list(dict.fromkeys(
        cid for cid in (g.complex(vid) for vid in vids) if g.parent(cid) is None))

    #Level determination
    levels = {}
    for root in roots:
        for vid in traversal.pre_order(g, root):
            levels[vid] = 0 if g.parent(vid) is None else levels[g.parent(vid)]+1

    #Component roots
    component_roots = {}
    for root in roots:
        for vid in traversal.pre_order(g, root):
            pid = g.parent(vid)
            if pid is None or g.complex(pid) != g.complex(vid):
                component_roots[vid] = True

    #Groups
    groups = {}
    nc = len(colors)
    count = 0
    for root in complex_roots:
        for vid in traversal.pre_order(g, root):
            groups[vid] = colors[count%nc]
            pid = g.parent(vid)
            if pid:
                if groups[vid] == groups[pid]:
                    groups[vid] = colors[(1789*count+17)%nc]
            count += 1

    #Nodes adding
    for vid in vids:
        shape = 'box' if vid in component_roots else 'circle'
        if labels is None:
            label_node = g.label(vid)
        else:
            label_node = labels[vid]
        level = levels[vid]
        if selection is None:
            color = groups[g.complex(vid)]
        else:
            color = '#fb7e81' if vid in selection else '#97c2fc'
        title = dict2html(g[vid], properties=properties)
        G.add_node(vid, shape=shape,
                    label=label_node,
                    level=level,
                    color=color,
                    title=title,
                    borderWidth=3,
                    )

    #Edges adding
    for edge in edges:
        label_edge = g.edge_type(edge[1])
        G.add_edge(edge[0], edge[1], label=label_edge, width=edge[2])

    return patch_show(G)

def patch_show(G, name=None):
    """Return the network page embedded in an HTML output.

    The page is in the iframe itself (srcdoc), with its scripts (cdn_resources
    'in_line'): it shows in notebooks and in static pages (documentation), each
    plot keeps its own graph, and no file is written (name is ignored; it was
    the name of the HTML file written by former versions).
    """
    page = G.generate_html(notebook=True)
    return iframe(page, f'width="{G.width}" height="{G.height}" style="border: none"')

