#!/usr/bin/env python3

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements.txt
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="rBrowser",
    version="1.0.0",
    author="Franky, neoemit",
    author_email="frankyros@gmail.com",
    description="Standalone NomadNet Browser - A web-based UI for exploring NomadNet nodes over the Reticulum network",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://github.com/fr33n0w/rBrowser",
    py_modules=["rBrowser"],
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Flask",
        "Intended Audience :: End Users/Desktop",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Communications",
        "Topic :: System :: Networking",
    ],
    keywords="reticulum nomadnet browser mesh network decentralized",
    python_requires=">=3.7",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "rBrowser=rBrowser:main",
        ],
    },
    project_urls={
        "Homepage": "https://github.com/fr33n0w/rBrowser",
        "Repository": "https://github.com/fr33n0w/rBrowser",
        "Issues": "https://github.com/fr33n0w/rBrowser/issues",
        "Documentation": "https://github.com/fr33n0w/rBrowser#readme",
    },
)
