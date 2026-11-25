import pathlib

import numpy as np
import pytest

encoding3d = pytest.importorskip("openalea.encoding3d")

from openalea.widgets.encoding3d import Encoding3D, frames, variables  # noqa: E402

data = pathlib.Path(__file__).parent.resolve() / "data" / "encoding3d"


def _objects(plot):
    return {obj.name: obj for obj in plot.objects}


def test_frame_colored_by_a_variable():
    plot = Encoding3D(data / "root_system.glb", variable="radius")
    roots = _objects(plot)["root_system mesh roots"]
    frame = encoding3d.read(str(data / "root_system.glb"))
    mesh = frame.data_structure("root_system").meshes[0]
    assert len(roots.vertices) == len(mesh.positions)
    assert len(roots.indices) * 3 == len(mesh.positions)
    radius = frame.data_structure("root_system").entity_set("SubOrgan").columns["radius"]
    assert list(roots.color_range) == [radius.min(), radius.max()]
    assert set(np.unique(roots.attribute)) <= set(radius.astype(np.float32))
    assert plot.colorbar_object_id == roots.id


def test_variable_of_a_coarser_scale():
    # the vertices refer to the segments, the axes and the plants
    plot = Encoding3D(data / "root_system.glb", variable="branching_order", entity_set="Axis")
    roots = _objects(plot)["root_system mesh roots"]
    orders = encoding3d.read(str(data / "root_system.glb")).data_structure("root_system").entity_set(
        "Axis").columns["branching_order"]
    assert list(roots.color_range) == [orders.min(), orders.max()]
    assert set(np.unique(roots.attribute)) == set(orders.astype(np.float32))


def test_without_variable():
    plot = Encoding3D(str(data / "root_system.glb"))
    roots = _objects(plot)["root_system mesh roots"]
    assert len(roots.attribute) == 0 and plot.colorbar_object_id == -1


def test_unknown_variable():
    with pytest.raises(ValueError, match="'nothing'.*radius"):
        Encoding3D(data / "root_system.glb", variable="nothing")


def test_regular_grid():
    plot = Encoding3D(data / "soil_and_roots.glb", variable="radius", grid_variable="soil_water_potential")
    objects = _objects(plot)
    soil = objects["soil grid"]
    frame = encoding3d.read(str(data / "soil_and_roots.glb"))
    grid = frame.data_structure("soil").grid
    cells = int(np.prod(grid.shape))
    assert len(soil.vertices) == 8 * cells and len(soil.indices) == 12 * cells
    assert soil.opacity < 1
    # the cells span the grid
    size = np.array(grid.shape) * np.array(grid.spacing)
    extent = soil.vertices.max(axis=0) - soil.vertices.min(axis=0)
    assert np.allclose(extent, size)
    # the legend is the plants' variable
    assert plot.colorbar_object_id == objects["root_system mesh roots"].id


def test_adaptive_grid():
    plot = Encoding3D(data / "adaptive_soil.glb", grid_variable="soil_water_potential")
    soil = _objects(plot)["soil grid"]
    cells = encoding3d.read(str(data / "adaptive_soil.glb")).data_structure("soil").entity_set("Cell")
    assert len(soil.vertices) == 8 * cells.count
    assert plot.colorbar_object_id == soil.id
    assert variables(encoding3d.read(str(data / "adaptive_soil.glb")), "grid") == {"soil": ["soil_water_potential"]}


def test_variables_of_the_meshes():
    found = variables(encoding3d.read(str(data / "root_system.glb")))
    assert set(found) == {"SubOrgan", "Axis", "Plant"}
    assert "radius" in found["SubOrgan"] and "branching_order" in found["Axis"]
    # not the graph's columns
    assert not {"id", "complex", "parent"} & set(found["SubOrgan"])


def test_instances():
    plot = Encoding3D(data / "instances.glb")
    objects = _objects(plot)
    assert set(objects) == {"root_system mesh roots", "root_system instances sections"}
    assert len(objects["root_system instances sections"].indices) > 0


def test_sequence_has_a_time_series():
    index = data / "growing_sequence" / "scene.fspm.json"
    assert [frame.time for frame in frames(index)] == [0., 1., 2.]
    plot = Encoding3D(index, variable="length")
    roots = _objects(plot)["root_system mesh roots"]
    assert sorted(roots.vertices) == ["0.0", "1.0", "2.0"]
    # the roots grow
    assert len(roots.vertices["0.0"]) < len(roots.vertices["2.0"])
    # one color range over the frames: the values shown
    shown = np.concatenate(list(roots.attribute.values()))
    assert list(roots.color_range) == pytest.approx([shown.min(), shown.max()])
    # the same from the folder, or from a list of frames
    assert sorted(_objects(Encoding3D(data / "growing_sequence"))["root_system mesh roots"].vertices) == \
        ["0.0", "1.0", "2.0"]
    assert len(frames(list(frames(index)))) == 3


def test_adds_to_a_plot():
    import k3d
    plot = k3d.plot()
    assert Encoding3D(data / "root_system.glb", plot=plot) is plot
    assert len(plot.objects) == 1


def test_snapshot():
    plot = Encoding3D(data / "growing_sequence", variable="length")
    plot.snapshot_type = "online"
    assert "<!doctype html>" in plot.get_snapshot()
