#!/usr/bin/env python
"""Minimal setup.py for Hybrid Element Retriever."""

from setuptools import setup, find_packages
import os

# Read README for long description
here = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()
except:
    long_description = 'Hybrid Element Retriever - Natural language web automation'

setup(
    name='hybrid-element-retriever',
    version='0.1.0',
    description='Natural language to XPath/CSS selector conversion',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/hybrid-element-retriever',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    python_requires='>=3.9',
    install_requires=[
        'numpy>=1.20.0',
        'pydantic>=1.8.0',
    ],
    extras_require={
        'playwright': ['playwright>=1.30.0'],
        'ml': [
            'onnxruntime>=1.10.0',
            'faiss-cpu>=1.7.0',
        ],
        'dev': [
            'pytest>=6.0.0',
            'black>=22.0.0',
            'flake8>=4.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'her=her.cli:main',
            'her-demo=examples.demo:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)