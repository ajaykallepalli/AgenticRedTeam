"""
Setup configuration for Agentic Red-Team Manager
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="agentic-redteam",
    version="0.1.0",
    author="Agentic Red Team Contributors",
    author_email="support@agenticredteam.com",
    description="Automated, Safe Adversarial Testing for Agentic Systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ajaykallepalli/AgenticRedTeam",
    project_urls={
        "Bug Tracker": "https://github.com/ajaykallepalli/AgenticRedTeam/issues",
        "Documentation": "https://agenticredteam.readthedocs.io/",
        "Source Code": "https://github.com/ajaykallepalli/AgenticRedTeam",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Security",
        "Topic :: Software Development :: Testing",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.12.0",
            "pytest-cov>=4.1.0",
            "black>=23.10.0",
            "flake8>=6.1.0",
            "mypy>=1.7.0",
            "isort>=5.12.0",
        ],
        "docs": [
            "sphinx>=7.2.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "redteam=src.cli:main",
            "redteam-server=src.api.server:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)