import setuptools

with open("Readme.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyimagetool-kgord831", # Replace with your own username
    version="0.0.2",
    author="Kyle Gordon",
    author_email="kgord831@gmail.com",
    description="Python Image Tool for multidimensional analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kgord831/PyImageTool",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        'PyQt5-sip>=4.19.18',
        'PyQt5>=5.12.3',
        'numpy>=1.17.4',
        'xarray>=0.14.1',
        'pyqtgraph==0.10.0'
    ],
    package_data={'pyimagetool': ['cmaps/*.npy', 'cmaps/*.jpg']}
)