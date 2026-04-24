from setuptools import setup, find_packages

setup(
    name='todo-app',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'pydantic>=2.5.0',
    ],
    entry_points={
        'console_scripts': [
            'todo=todo.cli:main',
        ],
    },
    python_requires='>=3.10',
)
