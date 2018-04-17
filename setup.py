from setuptools import setup


setup(
    name = 'importgraph',
    version = '0.1',
    description = 'Create graphs from your imports',
    py_modules=['importgraph'],
    license='MIT',
    python_requires='>=3',
    install_requires=['graphviz'],
)
