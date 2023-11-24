import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="PDECalculator",
    version="0.0.1",
    author="", # TODO
    author_email="", # TODO
    description="", # TODO
    packages = ["pdecalculator"],
    package_dir= { "pdecalculator": "src" },
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LQCAPF/PDE",
    install_requires=[ ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
)
