from setuptools import setup, find_packages
import os

# Read requirements
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f 
                   if line.strip() and not line.startswith('#')]

# Split into core and dev requirements
core_requirements = []
dev_requirements = []
is_dev = False
for req in requirements:
    if 'Development dependencies' in req:
        is_dev = True
    elif req and not req.startswith('#'):
        if is_dev:
            dev_requirements.append(req)
        else:
            core_requirements.append(req)

setup(
    name='her',
    version='1.0.0',
    description='Hybrid Element Retriever - Production-ready web element location framework',
    author='HER Team',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    python_requires='>=3.9',
    install_requires=core_requirements,
    extras_require={
        'dev': dev_requirements
    },
    entry_points={
        'console_scripts': [
            'her=her.cli:main',
        ],
    },
    package_data={
        'her': ['models/*.json', 'models/*.onnx'],
    },
    include_package_data=True,
)