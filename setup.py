import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="DAKimport",
    version="0.0.5",
    packages=setuptools.find_packages(),
    install_requires=["numpy>=1.18.4", "Pillow>=7.1.2", "pypng>=0.0.20"],
    python_requires='>=3.5',

    author="Tom Price",
    author_email="t0mpr1c3@gmail.com",

    description="convert Designaknit .stp and .pat knitting pattern files into images",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/t0mpr1c3/DAKimport",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
