#!/usr/bin/env python
"""Setup script for Hybrid Element Retriever."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="hybrid-element-retriever",
    version="0.1.0",
    description="A hybrid framework for translating natural language steps into robust UI actions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="you@example.com",
    url="https://github.com/abhilashMirupati/hybrid-element-retriever",
    license="MIT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "playwright==1.39.0",
        "faiss-cpu==1.7.3",
        "numpy==1.23.5",
        "py4j==0.10.9.7",
        "pydantic==1.10.12",
        "onnxruntime==1.15.0",
        "transformers==4.32.0",
        "tokenizers==0.13.3",
        "huggingface_hub==0.16.4",
        "types-requests==2.31.0.4",
    ],
    extras_require={
        "dev": [
            "pytest==7.4.0",
            "pytest-cov==4.1.0",
            "flake8==6.1.0",
            "black==23.7.0",
            "mypy==1.5.1",
        ]
    },
    entry_points={
        "console_scripts": [
            "her-act=her.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)