from setuptools import setup, find_packages

setup(
    name="browserrag",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "flask",
        "flask-cors",
        "sentence-transformers",
        "faiss-cpu",
        "python-dotenv",
        "requests",
        "numpy",
        "fastmcp",
        "pydantic",
        "markitdown-mcp"
    ],
) 