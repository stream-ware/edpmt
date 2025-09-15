#!/usr/bin/env python3
"""
Setup script for EDPMT (Electronic Device Protocol Management - Transparent)
A simplified, secure, universal hardware communication library.
"""

try:
    from setuptools import setup, find_packages
except ImportError:
    print("Error: setuptools is required. Install it with: pip install setuptools")
    import sys
    sys.exit(1)

from pathlib import Path

# Read README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = requirements_file.read_text().strip().split('\n')
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

setup(
    name="edpmt",
    version="1.0.3",
    author="Tom Sapletta",
    author_email="info@softreck.dev",
    description="EDPM Transparent - Simple, Secure, Universal Hardware Communication",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/stream-ware/edpmt",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering",
        "Topic :: System :: Hardware",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Communications",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
        "rpi": [
            "RPi.GPIO>=0.7.1",
            "smbus2>=0.4.1",
            "spidev>=3.5",
            "pyserial>=3.5",
        ],
        "all": [
            "RPi.GPIO>=0.7.1",
            "smbus2>=0.4.1", 
            "spidev>=3.5",
            "pyserial>=3.5",
        ],
    },
    entry_points={
        "console_scripts": [
            "edpmt=edpmt.cli:main",
            "edpmt-server=edpmt.cli:server_main",
            "edpmt-client=edpmt.cli:client_main",
        ],
    },
    include_package_data=True,
    package_data={
        "edpmt": ["*.html", "*.js", "*.css"],
    },
    keywords="hardware gpio i2c spi uart raspberry-pi iot embedded automation transparent secure",
    project_urls={
        "Bug Reports": "https://github.com/stream-ware/edpmt/issues",
        "Source": "https://github.com/stream-ware/edpmt",
        "Documentation": "https://github.com/stream-ware/edpmt/blob/main/README.md",
    },
)
