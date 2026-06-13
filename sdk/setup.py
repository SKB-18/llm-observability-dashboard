"""SDK setup configuration"""
from setuptools import setup, find_packages

setup(
    name="llm-observer",
    version="0.1.0",
    description="Python SDK for LLM Observability Dashboard – automatic logging for LLM API calls",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "anthropic>=0.7.0",
        "urllib3>=1.26.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "responses>=0.24.0",
        ]
    },
)
