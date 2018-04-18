# ImportGraph

This is a tool to build an import graph for a python module.

## Requirements

It is recommended that you use [graphviz](https://www.graphviz.org/) as a visualization tool to 
produce images out of the output of this application. You can install graphviz with
```
sudo apt-get install graphviz
```
Various other installation methods are available in the [download section](https://www.graphviz.org/download/) of the graphviz website.

## Installation

Importgraph is on PyPi, so you can simply run
```
pip install importgraph
```

You may also clone this repo and from the repo root directory run
```
pip install -e .
```

## Usage

The basic usage is:
```
python -m importgraph module [module ...]
```

This will import all the specified modules, watch all subsequent imports and
print a dot graph to stdout. You can pipe the output into graphviz to create a
graph. For example, to create an svg output use:

```
python -m importgraph some.module | dot -Tsvg > graph.svg
```

For an extended explanation of the usage and the usage please refer to
```
python -m importgraph --help
```
The command line interface is still very much subject to change, and this will provide you with the most up to date information.

## Example

Running
```
python importgraph.py -r ".*/flask/.*" flask | dot -Tsvg > graph.svg
```
will produce the following graph (provided that you have flask installed):

![Flask Import Graph](https://raw.githubusercontent.com/mmEissen/importgraph/master/documentation/graph.png)

## Development

This poject uses [pipenv](https://docs.pipenv.org/) for development. You can install pipenv with:

```
pip install pipenv
```

Or by following an alternative installation method from the [pipenv homepage](https://docs.pipenv.org/#install-pipenv-today).
To install all dependencies for development in a new virtual env run:

```
pipenv install -d 
```

To activate the venv run:

```
pipenv shell
```
