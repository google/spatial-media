# <a href="https://raw.githubusercontent.com/google/spatial-media/master/360-Videos-Metadata/360VideosMetadata.py" download>360VideosMetadata.py</a>
This is a simple python command line tool for manipulating spherical/360 metadata in MP4 and MKV files. This can be used to either validate the 360 metadata in a tagged spherical video or insert the metadata into an existing file. Support of MKV files requires FFmpeg to be installed on the system.

## Usage
    ./360VideosMetadata.py -h
Prints help.


    ./360VideosMetadata.py <input> [additional input]
For each file specified, prints any spherical metadata contained within.


    ./360VideosMetadata.py -i <input> <output>
Reads &lt;input&gt; and adds spherical / 360 metadata saving the altered copy to &lt;output&gt;. Input and output cannot be the same file.
