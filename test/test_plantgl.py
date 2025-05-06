import openalea.plantgl.all as pgl
from oawidgets.plantgl import PlantGL


def test_scene():
    scene = pgl.Scene()
    scene.add(pgl.Sphere(5))
    p = PlantGL(scene)

    assert p is not None
