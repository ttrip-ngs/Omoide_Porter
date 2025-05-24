#!/usr/bin/env python

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="video-copy-tool",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="動画・写真コピーユーティリティ（デバイス対応）",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/video-copy-tool",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Multimedia :: Video",
        "Topic :: System :: Archiving",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "video-copy-tool=src.cli.main_cli:main",
            "vct=src.cli.main_cli:main",
        ],
    },
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-qt>=4.2.0",
            "black>=23.0.0",
            "mypy>=1.5.0",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.yaml", "*.yml", "*.md", "*.txt"],
    },
) 