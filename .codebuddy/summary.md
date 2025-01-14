# Project Summary: Spatial Media

## Overview of Technologies Used
The project is primarily developed using **Python** and utilizes various libraries and frameworks to handle spatial media. The key technologies include:

- **Flask**: A micro web framework for Python, used for building web applications.
- **Gunicorn**: A Python WSGI HTTP server for UNIX, used to serve the Flask application.
- **PyInstaller**: A tool for converting Python applications into stand-alone executables.

## Purpose of the Project
The Spatial Media project is a collection of specifications and tools designed to facilitate the use of 360° video and spatial audio. It provides metadata specifications for spatial audio and spherical video, as well as tools for injecting this metadata into media files. The project aims to enhance the experience of immersive media by enabling proper handling and playback of spatial audio and video formats.

## List of Build/Configuration/Project Files
- **Build/Configuration Files:**
  - `/setup.py`: Configuration for packaging the project.
  - `/docker/Dockerfile`: Docker configuration file for building the application container.
  - `/docker/requirements.txt`: Lists the Python dependencies required by the application.

## Source Files Directory
The source files can be found in the following directories:
- `/spatialmedia`: Contains the main application code for spatial media metadata injection.
- `/spatial-audio`: Contains resources related to spatial audio, including ambisonic filters and HRIRs.
- `/docker`: Contains the application entry point (`app.py`), WSGI configuration (`wsgi.py`), and startup script (`startup.sh`).

## Documentation Files Location
Documentation files are located in the `/docs` directory, which includes:
- Metadata specifications for spatial audio and spherical video.
- Various images and RFC documents related to the project.

## Summary of Key Files
- **Main Application:**
  - `/spatialmedia/__init__.py`: Initializes the spatial media package.
  - `/spatialmedia/gui.py`: Contains the GUI implementation for the application.
  - `/spatialmedia/metadata_utils.py`: Utility functions for handling metadata.
  
- **Spatial Audio Resources:**
  - `/spatial-audio/README.md`: Documentation for spatial audio resources.
  - `/spatial-audio/raw-symmetric-cube-hrirs`: Contains HRIR files for binaural audio processing.
  
- **Documentation:**
  - `/docs/spatial-audio-rfc.md`: Specification for spatial audio metadata.
  - `/docs/spherical-video-rfc.md`: Specification for spherical video metadata.
  - `/docs/spherical-video-v2-rfc.md`: Updated specification for spherical video metadata.
  - `/docs/vr180.md`: Documentation for the VR180 video format.

This summary provides a comprehensive overview of the Spatial Media project, detailing its purpose, technologies, file structure, and documentation resources.