# spherical-metadata.py
This is a simple python command line tool for manipulating spherical/360 metadata in mp4 and mkv files. This can be used to either validate the 360 metadata in a tagged spherical video or insert the metadata into an existing file. Support of .mkv files requires ffmpeg to be install in the system.

## Installation
Support for .mkv files requires ffmpeg to be installed.

## Usage
    ./360VideosMetadata.py -h


    ./360VideosMetadata.py -p <input>
Prints any contained spherical metadata.


    ./360VideosMetadata.py -i <input> <output>
Reads &lt;input&gt; and adds spherical / 360 metadata saving the altered copy to &lt;output&gt;. Input and output cannot be the same file.

