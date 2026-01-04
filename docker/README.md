# Spatial Media Metadata Injector - Web Version

This is a modern Flask web application for injecting spatial media metadata, running inside Docker. It replaces the legacy Tkinter desktop application with a web browser interface.

## Features
- **Web Interface**: A clean, dark-mode web UI supporting drag-and-drop for multiple files.
    - **Progress Bar**: Visual indicator for file upload status.
- **Backend Refactor**: Logic ported from `gui.py` to a Python Flask application.
    - **Persistence**: Fixed storage path to persist uploads and processed files.
- **Docker Integration**: Builds directly from the local source code.
- **Headerless**: No dependency on X11 or GUI libraries in the container.

## How to Run

### Prerequisite
Ensure you have Docker installed.

### 1. Build the Image
Run this command from the **root of the repository** (the parent folder containing both `spatialmedia` and `docker` directories):

```bash
docker build -t spatial-media-web -f docker/Dockerfile .
```

### 2. Run the Container
We use the `--name` flag to assign a consistent name to the container, and a volume map to persist data locally.

**PowerShell example:**
```powershell
# Create a local folder for data (if it doesn't exist)
mkdir data -ErrorAction SilentlyContinue

# Run with volume mapping and container name
docker run -p 5000:5000 --name spatial-media-metadata-injector -v ${PWD}\data:/app/uploads spatial-media-web
```

**Bash/Mac/Linux example:**
```bash
# Run with volume mapping and container name
docker run -p 5000:5000 --name spatial-media-metadata-injector -v $(pwd)/data:/app/uploads spatial-media-web
```

### 3. Use the Tool
Open your browser and navigate to:
[http://localhost:5000](http://localhost:5000)

1.  **Drag and drop** your .mp4 or .mov files.
2.  Select the appropriate metadata options (360, 3D, Spatial Audio).
3.  Click **Inject Metadata**.
4.  Download the processed files via the web UI or find them in your local `data` folder.

## Troubleshooting

### "File Not Found" Error
Ensure you are using the volume mapping `-v ...:/app/uploads` as shown above. This ensures files are saved to a location that persists across the application lifecycle and is accessible to all worker threads.

### "Name already in use" Error
If you try to run the command again and get an error that the name `spatial-media-metadata-injector` is already in use, you need to remove the old container first:
```bash
docker rm -f spatial-media-metadata-injector
```
