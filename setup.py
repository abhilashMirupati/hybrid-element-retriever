"""Setup script for Hybrid Element Retriever."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip() 
        for line in requirements_file.read_text().splitlines() 
        if line.strip() and not line.startswith("#")
    ]

# Read dev requirements
dev_requirements_file = Path(__file__).parent / "requirements-dev.txt"
dev_requirements = []
if dev_requirements_file.exists():
    dev_requirements = [
        line.strip() 
        for line in dev_requirements_file.read_text().splitlines() 
        if line.strip() and not line.startswith("#") and not line.startswith("-r")
    ]

setup(
    name="hybrid-element-retriever",
    version="1.0.0",
    author="HER Team",
    author_email="her@example.com",
    description="Production-ready natural language element location for web automation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/her",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/her/issues",
        "Documentation": "https://her.readthedocs.io",
        "Source Code": "https://github.com/yourusername/her",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "her": [
            "models/.gitkeep",
            "*.json",
        ],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
        "playwright": ["playwright>=1.30.0"],
        "all": requirements + dev_requirements + ["playwright>=1.30.0"],
    },
    entry_points={
        "console_scripts": [
            "her=her.cli:main",
            "her-gateway=her.gateway_server:main",
        ],
    },
    zip_safe=False,
)