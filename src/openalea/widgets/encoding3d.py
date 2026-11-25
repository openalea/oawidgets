"""Display encoding3d scenes (functional-structural plant model scenes, based on glTF) with k3d.

Encoding3D returns a k3d plot of a frame (one time step of a scene) or of a
sequence of frames, with a time slider:

- the meshes of the plants, colored by a variable of their entities (any scale
  the vertices refer to, such as the radius of root segments or the PAR of leaf
  parts);
- the instances of shared templates, placed;
- the grids of the environment (soil...), as translucent cells colored by a
  variable.

See https://encoding3d.readthedocs.io for the format and openalea.encoding3d.
"""
import os

import k3d
import numpy as np

try:
    from openalea import encoding3d
    from openalea.encoding3d.instances import placed_meshes
    from openalea.encoding3d.model import NO_ID
except ImportError as error:
    raise ImportError(
        "openalea.widgets.encoding3d displays encoding3d scenes, and needs openalea.encoding3d: "
        "mamba install -c openalea3 -c conda-forge openalea.encoding3d"
    ) from error

# color of the shapes without values (and of all of them without a variable)
NO_VALUE_COLOR = 0xB0B0B0


def frames(scene):
    """The frames of *scene*, in time order.

    Parameters
    ----------
    scene : Frame, str or list of Frame
        A frame, the path of a frame (.glb, or a member of a .fspm.zip archive),
        the path of a sequence (its index scene.fspm.json, its folder or its
        archive), or a list of frames.

    Returns
    -------
    list of Frame
    """
    if isinstance(scene, encoding3d.Frame):
        return [scene]
    if isinstance(scene, (str, os.PathLike)):
        path = os.fspath(scene)
        if path.endswith(".glb"):
            return [encoding3d.read(path)]
        return list(encoding3d.read_sequence(path))
    return list(scene)


def _numeric_scalars(table):
    """The numeric scalar variables of a table (not its reserved columns: id, graph, grid index...)."""
    return [name for name in table.variable_names()
            if np.ndim(table.columns[name]) == 1 and np.issubdtype(np.asarray(table.columns[name]).dtype, np.number)]


def variables(frame, kind="mesh"):
    """The variables that can color the shapes of a frame.

    Parameters
    ----------
    frame : Frame
    kind : str, optional
        'mesh' for the variable of Encoding3D (by entity set the meshes refer
        to), 'grid' for its grid_variable (by grid).

    Returns
    -------
    dict
        {entity set or grid name: list of variable names}
    """
    found = {}
    for data_structure in frame.data_structures:
        if kind == "grid":
            if data_structure.grid is not None:
                found[data_structure.id] = _numeric_scalars(data_structure.entity_set(data_structure.grid.cells))
            continue
        for mesh in data_structure.meshes:
            for name in mesh.feature_rows:
                found.setdefault(name, _numeric_scalars(data_structure.entity_set(name)))
    return found


def _transform(points, origin):
    """Points (n, 3) moved by a data structure's origin (4x4)."""
    origin = np.asarray(origin, dtype=np.float64)
    if np.array_equal(origin, np.eye(4)):
        return points
    return points @ origin[:3, :3].T + origin[:3, 3]


def _vertex_values(data_structure, mesh, variable, entity_set=None):
    """The value of *variable* at each vertex of *mesh* (NaN without one), from
    the entity set *entity_set*, or the first one the vertices refer to that
    has the variable (as openalea.encoding3d.display.add_display). None if no
    entity set of the mesh has it."""
    candidates = [entity_set] if entity_set else list(mesh.feature_rows)
    for name in candidates:
        if name not in mesh.feature_rows:
            continue
        table = data_structure.entity_set(name)
        if variable not in table.columns:
            continue
        values = np.asarray(table.columns[variable], dtype=np.float64)
        if values.ndim != 1:
            raise ValueError(f"'{variable}' of {name} is a vector: only scalars can color the shapes")
        rows = mesh.feature_rows[name]
        at_vertices = np.full(rows.size, np.nan)
        at_vertices[rows != NO_ID] = values[rows[rows != NO_ID]]
        return at_vertices
    return None


def _box_triangles(lower, upper):
    """Vertices (8n, 3) and triangles (12n, 3) of n boxes, from their corners (n, 3)."""
    corners = np.stack([np.stack([np.where(x, upper[:, 0], lower[:, 0]),
                                  np.where(y, upper[:, 1], lower[:, 1]),
                                  np.where(z, upper[:, 2], lower[:, 2])], axis=1)
                        for z in (0, 1) for y in (0, 1) for x in (0, 1)], axis=1)   # (n, 8, 3)
    faces = np.array([[0, 2, 1], [1, 2, 3], [4, 5, 6], [5, 7, 6],      # z-, z+
                      [0, 1, 4], [1, 5, 4], [2, 6, 3], [3, 6, 7],      # y-, y+
                      [0, 4, 2], [2, 4, 6], [1, 3, 5], [3, 7, 5]])     # x-, x+
    triangles = faces[None, :, :] + 8 * np.arange(len(lower))[:, None, None]
    return corners.reshape(-1, 3), triangles.reshape(-1, 3)


def _cells(data_structure):
    """The corners (lower, upper: (n, 3)) of the cells of a grid, by row of its cells' entity set."""
    grid = data_structure.grid
    cells = data_structure.entity_set(grid.cells)
    dimensions = len(grid.shape)
    spacing = np.array(tuple(grid.spacing) + (1.,) * (3 - dimensions), dtype=np.float64)
    origin = np.array(tuple(grid.origin) + (0.,) * (3 - dimensions), dtype=np.float64)
    if grid.kind == "regular":
        shape = tuple(grid.shape) + (1,) * (3 - dimensions)
        index = np.stack(np.unravel_index(np.arange(cells.count), shape), axis=1).astype(np.float64)
        size = np.broadcast_to(spacing, index.shape)
    else:  # adaptive: the leaf cells, each with its level and index
        level = np.asarray(cells.columns["level"], dtype=np.int64)
        index = np.asarray(cells.columns["index"], dtype=np.float64).reshape(cells.count, -1)
        index = np.pad(index, ((0, 0), (0, 3 - index.shape[1])))
        size = spacing[None, :] / (2. ** level)[:, None]
    lower = origin[None, :] + index * size
    upper = lower + size
    if not grid.z_up:
        lower[:, 2], upper[:, 2] = -upper[:, 2], -lower[:, 2]
    return lower, upper


def _shapes(frame, variable, entity_set, grid_variable):
    """The shapes of a frame: {key: (vertices, triangles, values or None, kind)}, kind 'mesh' or 'grid'."""
    shapes = {}
    for data_structure in frame.data_structures:
        for number, mesh in enumerate(data_structure.meshes):
            triangles = (mesh.indices if mesh.indices is not None else np.arange(len(mesh.positions))).reshape(-1, 3)
            values = None if variable is None else _vertex_values(data_structure, mesh, variable, entity_set)
            shapes[(data_structure.id, "mesh", mesh.name or number)] = (
                _transform(mesh.positions, data_structure.origin), triangles, values, "mesh")
        for instance_set in data_structure.instance_sets:
            placed = placed_meshes(frame, data_structure, instance_set)
            shapes[(data_structure.id, "instances", instance_set.name)] = (
                _transform(placed.positions, data_structure.origin), placed.triangles, None, "mesh")
        if data_structure.grid is not None:
            cells = data_structure.entity_set(data_structure.grid.cells)
            values = None
            if grid_variable is not None and grid_variable in cells.columns:
                values = np.repeat(np.asarray(cells.columns[grid_variable], dtype=np.float64), 8)
            lower, upper = _cells(data_structure)
            vertices, triangles = _box_triangles(lower, upper)
            shapes[(data_structure.id, "grid")] = (_transform(vertices, data_structure.origin), triangles, values,
                                                    "grid")
    return shapes


def _split(vertices, triangles, values):
    """(colored, plain): the triangles whose vertices all have a value, and the others, each as (vertices, triangles,
    values) with only the vertices they use."""
    def subset(kept):
        used, compact = np.unique(triangles[kept], return_inverse=True)
        return vertices[used], compact.reshape(-1, 3), None if values is None else values[used]
    if values is None:
        return None, subset(np.ones(len(triangles), dtype=bool))
    known = np.isfinite(values)[triangles].all(axis=1)
    return (subset(known) if known.any() else None), (subset(~known) if not known.all() else None)


def _series(items, timed):
    """k3d time series ({time: array}) of a list of (time, array) if *timed* (a sequence), else the array of the
    single frame."""
    if not timed:
        return items[0][1]
    return {str(time): array for time, array in items}


def Encoding3D(scene, variable=None, entity_set=None, grid_variable=None, plot=None,
               color_map=None, color_range=None, color=NO_VALUE_COLOR, grid_opacity=0.25):
    """Plot an encoding3d scene: a frame, or a sequence of frames.

    Parameters
    ----------
    scene : Frame, str or list of Frame
        A frame, a path (frame .glb, sequence index scene.fspm.json, its folder
        or its .fspm.zip archive), or a list of frames (see frames).
    variable : str, optional
        Variable coloring the meshes, from the entity set *entity_set*, or the
        first one the vertices refer to that has it (for instance the segments,
        then the axes, then the plants). Shapes without a value are in *color*.
    entity_set : str, optional
        Name of the entity set holding *variable* (such as 'SubOrgan').
    grid_variable : str, optional
        Variable of the cells coloring the grids (such as
        'soil_water_potential'). Grids are in *color* without it.
    plot : k3d plot, optional
        Plot to add the scene to. A new plot if None.
    color_map : k3d color map, optional
        Viridis by default.
    color_range : (float, float), optional
        Values of the ends of the color map, for *variable* and
        *grid_variable*: their range over the frames by default.
    color : int, optional
        Color of the shapes without value, as 0xRRGGBB.
    grid_opacity : float, optional
        Opacity of the grids' cells.

    Returns
    -------
    plot : k3d plot
        With a time slider for a sequence (the frames' times).
    """
    if plot is None:
        plot = k3d.plot()
    if color_map is None:
        color_map = k3d.colormaps.matplotlib_color_maps.Viridis
    sequence = frames(scene)
    if not sequence:
        raise ValueError("the scene has no frame")
    by_frame = [(float(frame.time or 0.), _shapes(frame, variable, entity_set, grid_variable)) for frame in sequence]
    keys = list(dict.fromkeys(key for _, shapes in by_frame for key in shapes))
    for name, kind in ((variable, "mesh"), (grid_variable, "grid")):
        if name is not None and not any(values is not None for _, shapes in by_frame
                                        for (_, _, values, k) in shapes.values() if k == kind):
            raise ValueError(f"no {'mesh' if kind == 'mesh' else 'grid'} of the scene has the variable '{name}'; "
                             f"variables: {variables(sequence[0], kind)}")

    def value_range(kind):
        values = [v[np.isfinite(v)] for _, shapes in by_frame for (_, _, v, k) in shapes.values()
                  if k == kind and v is not None]
        values = np.concatenate(values) if values else np.empty(0)
        if values.size == 0:
            return None
        return (float(values.min()), float(values.max()) if values.max() > values.min() else float(values.min()) + 1.)

    ranges = {kind: color_range or value_range(kind) for kind in ("mesh", "grid")}
    timed = len(by_frame) > 1
    colored_objects = {"mesh": [], "grid": []}
    for key in keys:
        present = [(time, shapes[key]) for time, shapes in by_frame if key in shapes]
        kind = present[0][1][3]
        opacity = grid_opacity if kind == "grid" else 1.
        parts = [(time,) + _split(*shape[:3]) for time, shape in present]
        name = " ".join(str(item) for item in key)
        colored = [(time, part) for time, part, _ in parts if part is not None]
        if colored and ranges[kind] is not None:
            obj = k3d.mesh(_series([(t, p[0].astype(np.float32)) for t, p in colored], timed),
                           _series([(t, p[1].astype(np.uint32)) for t, p in colored], timed),
                           attribute=_series([(t, p[2].astype(np.float32)) for t, p in colored], timed),
                           color_map=color_map, color_range=list(ranges[kind]), opacity=opacity,
                           side="double", name=name)
            plot += obj
            colored_objects[kind].append(obj)
        plain = [(time, part) for time, _, part in parts if part is not None]
        if plain:
            plot += k3d.mesh(_series([(t, p[0].astype(np.float32)) for t, p in plain], timed),
                             _series([(t, p[1].astype(np.uint32)) for t, p in plain], timed),
                             color=color, opacity=opacity, side="double",
                             name=name + (" (no value)" if variable or grid_variable else ""))
    # the color legend: of the plants' variable, else of the grids'
    legend = colored_objects["mesh"] + colored_objects["grid"]
    if legend:
        plot.colorbar_object_id = legend[0].id
    plot.lighting = 3
    return plot
