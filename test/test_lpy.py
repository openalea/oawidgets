import pytest

from IPython.testing.globalipapp import start_ipython


@pytest.fixture(scope="session")
def session_ip():
    yield start_ipython()


@pytest.fixture(scope="function")
def ip(session_ip):
    session_ip.run_line_magic(magic_name="load_ext", line="oawidgets.lpymagic")
    yield session_ip
    session_ip.run_line_magic(magic_name="unload_ext", line="oawidgets.lpymagic")
    session_ip.run_line_magic(magic_name="reset", line="-f")


def test_lpy(ip):
    ip.run_cell(
        raw_cell="""
    from oawidgets import lpymagic, plantgl
    from random import *
    p1 = 0.550000 
    p2 = 0.450000
    axiom = '_(1)[f(50)+90f(10)]-(90)P(1,0)'
    """)
    cell = """


#Axiom: F(1)
derivation length: 100

# A = branching state
# B = non-branching state 

def Start():
    global m
    m = 0

production:

P(x,t) :
    if t <= 10 : produce T[G(x)]P(x,t+1)
    else  :
        global m
        m = 1
        produce *

G(x) : 
    if m==1 :
        produce +(90)S(x)

S(x) :
    if random() <= 0.5: produce A(x)
    else: produce B(x)

A(x) : 
    if random() <= p1: produce I[M(x)]A(1-x)
    else: produce IB(1-x)

B(x) :
    if random() <= p2: produce IB(1-x)
    else: produce I[M(x)]A(1-x)

homomorphism:

T :    produce ;(1)f(40);(1)@c(1)
M(x) : 
    if x==0 :   produce ;(2)+F(20)
    elif x==1 : produce ;(2)-F(20)

I    : produce ;(1)F(2)
A(x) : produce ;(1)@O(3)
B(x) : produce ;(2)@O(3)

endlsystem
        """
    ip.run_cell_magic(magic_name="lpy", line='-i * -w axiom -n 100 -s scene', cell=cell)
