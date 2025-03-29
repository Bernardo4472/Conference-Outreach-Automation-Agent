#!/usr/bin/env python3
"""
Setup script for the Conference Outreach Automation Agent.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="conference-outreach-agent",
    version="0.1.0",
    author="WhyAI",
    author_email="your.email@example.com",
    description="An automated tool for finding and contacting event organizers for relevant tech conferences",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/conference-outreach-agent",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "conference-agent=cli:main",
        ],
    },
)
