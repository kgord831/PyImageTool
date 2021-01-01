import setuptools
from pathlib import Path

setup_path = Path(__file__).parent

with open(Path(setup_path, 'Readme.md'), "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyimagetool",
    version="1.0",
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
    python_requires='>=3.7.9',
    install_requires=[
        'numpy',
        'pyqtgraph',
        'scipy',
        'Pillow'
    ],
    package_data={'pyimagetool': ['cmaps/data/scivis_cmaps/*.xml',
                                  'cmaps/data/CETperceptual_csv_0_255/*.csv',
                                  'cmaps/data/*.npy', 'cmaps/data/*.jpg',
                                  'data/*.npy']}
)
