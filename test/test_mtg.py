import openalea
from openalea.deploy.shared_data import shared_data
from openalea.mtg import MTG
from oawidgets.mtg import plot


def test_mtg():
    data = shared_data(openalea.mtg)
    g = MTG(data / "boutdenoylum2.mtg")
    plot(g)
