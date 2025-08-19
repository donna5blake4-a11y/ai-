#!/usr/bin/env python3
"""
Setup script for AI Deals Manager
"""

from setuptools import setup, find_packages
import os

# قراءة README
def read_readme():
    with open("README.md", "r", encoding="utf-8") as f:
        return f.read()

# قراءة requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="ai-deals-manager",
    version="1.0.0",
    author="AI Deals Team",
    author_email="support@aideals.com",
    description="نظام إدارة العروض الذكي مع دعم AI",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-repo/ai-deals-manager",
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
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Office/Business :: Financial",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "gui": [
            "customtkinter>=5.2.0",
            "Pillow>=10.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ai-deals=ai_deals_manager:main",
            "ai-deals-test=test_ai_system:main",
            "ai-deals-run=run_ai_system:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.md", "*.txt"],
    },
    keywords=[
        "amazon", "deals", "ai", "telegram", "bot", "price", "comparison",
        "egypt", "jumia", "noon", "scraping", "database", "sqlite"
    ],
    project_urls={
        "Bug Reports": "https://github.com/your-repo/ai-deals-manager/issues",
        "Source": "https://github.com/your-repo/ai-deals-manager",
        "Documentation": "https://github.com/your-repo/ai-deals-manager/blob/main/README.md",
    },
)