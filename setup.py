#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='spatialmedia',
    version='2.1.0',
    description='Specifications and tools for 360 video and spatial audio.',
    long_description='Tools for examining and injecting spatial media metadata in MP4/MOV files. Supports 360 video, stereoscopic 3D, and spatial audio (ambisonics).',
    author='Google Inc',
    license='Apache License 2.0',
    url='https://github.com/google/spatial-media',
    python_requires='>=3.8',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'spatialmedia=spatialmedia.__main__:main',
        ],
        'gui_scripts': [
            'spatialmedia-gui=spatialmedia.gui:main',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Multimedia :: Video',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
    ],
    install_requires=[],
    extras_require={
        'build': [
            'PyInstaller>=6.0.0',
            'pillow>=10.0.0',
            'packaging>=23.0',
        ],
    },
)
