import setuptools
import os
from io import open
from setuptools.command.install import install

src_dir = os.path.abspath(os.path.dirname(__file__))

with open("README.md", "r") as fh:
    long_description = fh.read()

# Build requirements
requirements_path = f"{src_dir}/requirements.txt"
requirements = []
if os.path.isfile(requirements_path):
    with open(requirements_path) as f:
        requirements = f.read().splitlines()

setuptools.setup(
    name="gamebench",
    version="0.0.1",
    author="Joshua Clymer",
    author_email="joshuamclymer@gmail.com",
    description="A benchmark for testing AI agents in multiplayer games",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Joshuaclymer/GameBench",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
    install_requires=requirements,
    packages=['agents', 'games', 'api'],
    package_data={'GameBench': ['LICENCE', 'requirements.txt']},
)