from setuptools import find_packages, setup
from pathlib import Path

def read_version():
    ns = {}
    path = Path("signlang_segmenter") / "_version.py"
    with path.open("r", encoding="utf-8") as f:
        exec(f.read(), ns)
    return ns["__version__"]

version = read_version()

setup(
    name="signlang-segmenter",
    version=version,
    description="A Python library for sign language video and pose segmentation.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Mohamed Yehia",
    url="https://github.com/24-mohamedyehia/signlang-segmenter",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "opencv-python==4.11.0.86",
        "numpy==1.26.4",
        "matplotlib==3.7.3"
    ],
    extras_require={
        "dev": [
        "notebook==6.5.4"
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
