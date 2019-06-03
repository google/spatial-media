# Spatial Media

A collection of specifications and tools for 360&deg; video and spatial audio, including:

- [Spatial Audio](docs/spatial-audio-rfc.md) metadata specification
- [Spherical Video](docs/spherical-video-rfc.md) metadata specification
- [Spherical Video V2](docs/spherical-video-v2-rfc.md) metadata specification
- [VR180 Video Format](docs/vr180.md) VR180 video format
- [Spatial Media tools](spatialmedia/) for injecting spatial media metadata in media files

## CLI
```
$ python3 ./spatialmedia/cli.py -h
usage: cli.py [-h] -i I -o O [-s] [-a]

Add 3D video metadata

optional arguments:
  -h, --help  show this help message and exit
  -i I        The input video
  -o O        The output video
  -s          Stereoscopic Top/Bottom Video
  -a          Spatial Audio
```