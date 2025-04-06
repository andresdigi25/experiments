"""
Setup script for the Scrum Master Bot package
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="scrummaster",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A simple NLP-powered assistant for daily standups",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/scrummaster",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "nltk>=3.6.0",
        "textual>=0.11.0",
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "pydantic>=1.8.0",
    ],
    entry_points={
        "console_scripts": [
            "scrummaster-cli=scrummaster.cli:main",
            "scrummaster-api=scrummaster.api:start_api",
        ],
    },
)