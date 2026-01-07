#!/usr/bin/env python3
"""Setup script for Spatial Media tools."""

from setuptools import setup, find_packages

setup(
    name='spatialmedia',
    version='2.1.0',
    description='Specifications and tools for 360 video and spatial audio.',
    long_description='Tools for examining and injecting spatial media metadata in MP4/MOV files.',
    author='Google Inc',
    license='Apache License 2.0',
    url='https://github.com/google/spatial-media',
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=[
        # No external dependencies for core functionality
    ],
    extras_require={
        'build': [
            'PyInstaller>=5.0',
            'pillow>=9.0',
            'packaging>=21.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'spatialmedia=spatialmedia.__main__:main',
        ],
        'gui_scripts': [
            'spatialmedia-gui=spatialmedia.gui:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Multimedia :: Video',
    ],
)
