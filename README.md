# ImportGraph

This is a tool to build an import graph for a python module.

## Usage

The basic usage is:
```
importgraph.py module [module ...]
```

This will import all the specified modules, watch all subsequent imports and
print a dot graph to stdout. You can pipe the output into graphviz to create a
graph. For example, to create an svg output use:

```
importgraph.py some.module | dot -Tsvg > graph.svg
```

For example, running
```
python importgraph.py -r ".*/flask/.*" flask | dot -Tsvg > graph.svg
```
will produce the following graph:
![Flask Import Graph](https://raw.githubusercontent.com/mmEissen/importgraph/master/documentation/graph.png)
