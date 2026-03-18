"""
Medical Record Interpreter - 安装配置
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="medical-record-inspector",
    version="0.1.0",
    author="ChaosForge Agent",
    author_email="agent@chaosforge.org",
    description="Medical Record Inspector - 让病历自我审查的质控工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/medical-record-inspector",
    project_urls={
        "Bug Tracker": "https://github.com/your-org/medical-record-inspector/issues",
        "Documentation": "https://github.com/your-org/medical-record-inspector/docs",
    },
    packages=find_packages(where="."),
    package_dir={"": "."},
    py_modules=["src.inspector", "src.cli", "src.api"],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "mypy>=1.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "pylint>=3.0.0",
        ],
        "api": [
            "fastapi>=0.100.0",
            "uvicorn>=0.23.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "medical-inspector=src.cli:main",
            "mri-cli=src.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="medical, records, quality, control, ai, nlp",
    include_package_data=True,
)
