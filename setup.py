from setuptools import setup
import os

name='mtluakernel'

here = os.path.abspath(os.path.dirname(__file__))
ns = {}
with open(os.path.join(here, name, '_version.py')) as f:
    exec(f.read(), ns)
version = ns['__version__']

setup(
    name=name,
    version=version,
    description='Minetest Lua Kernel for Jupyter',
    packages=[name],
    install_requires=['ipykernel'],
)
