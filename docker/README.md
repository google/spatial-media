This is the first attempt at taking a different path for the Spatial Media Tools and creating a Docker container to use the [CLI commands](https://github.com/google/spatial-media/tree/master/spatialmedia#spatial-media-metadata-injector) to inject the Spatial Media metadata required for VR360/180 video with or without ambisonic audio.

This should remove any OS specific requirements for Python TK that are tied to different Python versions in use. It will be based on the latest available Python/Alpine image at the time of release.

To build this image clone this repository to a machine with Docker installed and run the following from this ./docker folder where the Dockerfile exists:

`docker build -t spatialmedia/tools .`

To run this newly built image in Docker use the following command:

**Note:** Map an OS path in the first section of the -v flag to /app/data within the container and ensure that it has read/write access.

```
docker run -it \
-p 8888:5000 \
--net=bridge \
-h spatialmedia \
--name SpatialMediaTools \
-v /path/to/OS/folder:/spatialmediatools/app/data \
-d spatialmedia/tools
```

Once the image is running copy a file to inject to the above OS path and run the following to connect to the running image:

`docker exec -it SpatialMediaTools sh`

Change to the directory where the code was installed to in the image:

`cd spatial-media-master`

Using the [CLI commands](https://github.com/google/spatial-media/tree/master/spatialmedia#spatial-media-metadata-injector) as a reference attempt to inject the spatial media metadata into the video file you copied to the above path. Example:

`python spatialmedia -i /spatialmediatools/app/data/<name_of_input_file.ext> /spatialmediatools/app/data/<name_of_output_file.ext>`
