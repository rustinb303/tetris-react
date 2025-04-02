from setuptools import setup, find_packages

setup(
    name="crewai-multi-agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "crewai>=0.108.0",
        "crewai-tools>=0.38.1",
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
    ],
    python_requires=">=3.10",
    description="A flexible framework for creating and managing multi-agent systems using CrewAI",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/crewai-multi-agent-project",
)
