# <a href="https://github.com/google/spatial-media/archive/master.zip" download>master.zip</a>
This is a simple python command line tool for manipulating spherical/360 metadata in MP4 files. This can be used to either validate the 360 metadata in a tagged spherical video or insert the metadata into an existing file.

## Installation
Download the script <a href="https://github.com/google/spatial-media/archive/master.zip" download>master.zip</a> and install <a href="https://www.python.org/download/releases/2.7.7/">Python 2.7</a>.


## Usage
    python spatialmedia -h
Prints help.


     <input> [additional input]
For each file specified, prints any spherical metadata contained within.


    python spatialmedia -i [--stereo=(top-bottom|left-right)] <input> <output>
Reads &lt;input&gt; and adds spherical / 360 metadata saving the altered copy to &lt;output&gt;. Input and output cannot be the same file. Options top-bottom and left-right flags set the appropriate values for the StereoMode tag.

