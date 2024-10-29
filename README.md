# Spatial Media

A collection of specifications and tools for 360&deg; video and spatial audio, including:

- [Spatial Audio](docs/spatial-audio-rfc.md) metadata specification
- [Spherical Video](docs/spherical-video-rfc.md) metadata specification
- [Spherical Video V2](docs/spherical-video-v2-rfc.md) metadata specification
- [VR180 Video Format](docs/vr180.md) VR180 video format
- [Spatial Media tools](spatialmedia/) for injecting spatial media metadata in media files

## Recent Updates: Multi-File Processing Support

The GUI application has been enhanced with batch processing capabilities. Here are the key improvements:

### New Features

1. **Multiple File Selection**
   - Users can now select multiple files simultaneously
   - First selected file is displayed in the UI for reference

2. **Simplified Output Handling**
   - Single output directory selection for all files
   - Automatic file naming with "_injected" suffix

3. **Batch Processing**
   - Sequential processing of all selected files
   - Robust error handling: individual failures don't stop the batch
   - Progress tracking with status messages

### Technical Implementation

The changes were implemented in `spatialmedia/gui.py`:

```python
# Enable multiple file selection
self.open_options["multiple"] = True

# Process multiple files
for input_file in self.all_files:
    output_file = os.path.join(
        os.path.dirname(self.save_file),
        f"{split_filename[0]}_injected{split_filename[1]}"
    )
    metadata_utils.inject_metadata(input_file, output_file, metadata, console.append)
```

These updates significantly improve workflow efficiency when processing multiple videos.