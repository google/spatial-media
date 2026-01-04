document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const inputElement = dropZone.querySelector('input');
    const fileList = document.getElementById('file-list');
    const controls = document.getElementById('controls');
    const injectBtn = document.getElementById('inject-btn');
    const sphericalCb = document.getElementById('spherical');
    const cb3d = document.getElementById('3d');
    const cbAudio = document.getElementById('spatial-audio');
    const statusMessage = document.getElementById('status-message');
    const resultsArea = document.getElementById('results-area');
    const downloadLinks = document.getElementById('download-links');

    // Progress UI
    const progressContainer = document.getElementById('progress-container');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');

    let uploadedFiles = [];

    // Drag and Drop Logic
    dropZone.addEventListener('click', () => inputElement.click());

    inputElement.addEventListener('change', (e) => {
        if (inputElement.files.length) {
            handleFiles(inputElement.files);
        }
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drop-zone--over');
    });

    ['dragleave', 'dragend'].forEach(type => {
        dropZone.addEventListener(type, () => {
            dropZone.classList.remove('drop-zone--over');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drop-zone--over');
        if (e.dataTransfer.files.length) {
            handleFiles(e.dataTransfer.files);
        }
    });

    async function handleFiles(files) {
        const formData = new FormData();
        // Append all files
        for (let i = 0; i < files.length; i++) {
            formData.append('files[]', files[i]);
        }

        statusMessage.textContent = 'Uploading and analyzing...';
        progressContainer.classList.remove('hidden');
        progressFill.style.width = '0%';
        progressText.textContent = '0%';

        try {
            const data = await uploadFilesValues(formData);

            // Merge new files with existing list if you want cumulative upload, 
            // but here we might just replace or add. Let's add.
            data.files.forEach(f => {
                if (f.logs && f.logs.length > 0) {
                    // Check for errors in logs
                    const errors = f.logs.filter(l => l.toLowerCase().includes('error') || l.toLowerCase().includes('warning'));
                    if (errors.length > 0) {
                        console.warn(`Logs for ${f.filename}:`, f.logs);
                    }
                }
            });
            uploadedFiles = [...uploadedFiles, ...data.files];

            updateFileList();
            updateControlsState();
            statusMessage.textContent = '';
            controls.classList.remove('disabled');

        } catch (error) {
            console.error(error);
            statusMessage.textContent = 'Error uploading files.';
        } finally {
            progressContainer.classList.add('hidden');
        }
    }

    function uploadFilesValues(formData) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/upload', true);

            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    progressFill.style.width = percentComplete + '%';
                    progressText.textContent = Math.round(percentComplete) + '%';
                }
            };

            xhr.onload = () => {
                if (xhr.status === 200) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        resolve(response);
                    } catch (e) {
                        reject(e);
                    }
                } else {
                    reject(new Error(xhr.statusText));
                }
            };

            xhr.onerror = () => reject(new Error('Network Error'));

            xhr.send(formData);
        });
    }

    function updateFileList() {
        fileList.innerHTML = '';
        uploadedFiles.forEach(file => {
            const item = document.createElement('div');
            item.classList.add('file-item');

            item.innerHTML = `
                <div class="file-info">
                    <span class="file-name">${file.filename}</span>
                    <span class="file-meta">Ready to process</span>
                </div>
            `;
            fileList.appendChild(item);
        });
    }

    // UI Logic
    sphericalCb.addEventListener('change', updateControlsState);

    function updateControlsState() {
        if (uploadedFiles.length === 0) {
            controls.classList.add('disabled');
            return;
        }

        if (sphericalCb.checked) {
            cb3d.disabled = false;
            cb3d.parentElement.style.opacity = '1';
        } else {
            cb3d.disabled = true;
            cb3d.checked = false;
            cb3d.parentElement.style.opacity = '0.5';
        }

        // Auto-check spatial audio if any uploaded file supports it?
        // For now, leave manual.
    }

    // Initial Sync
    updateControlsState();

    // Inject Logic
    injectBtn.addEventListener('click', async () => {
        injectBtn.disabled = true;
        injectBtn.textContent = 'Processing...';
        statusMessage.textContent = 'Injecting metadata...';
        resultsArea.classList.add('hidden');
        downloadLinks.innerHTML = '';

        const options = {
            spherical: sphericalCb.checked,
            stereo: cb3d.checked,
            spatial_audio: cbAudio.checked
        };

        const filesToProcess = uploadedFiles.map(f => f.filename);

        try {
            const response = await fetch('/inject', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    files: filesToProcess,
                    options: options
                })
            });

            if (!response.ok) throw new Error('Injection failed');

            const data = await response.json();

            resultsArea.classList.remove('hidden');

            data.results.forEach(result => {
                if (result.success) {
                    const link = document.createElement('a');
                    link.href = result.output_url;
                    link.classList.add('download-link');
                    link.textContent = `Download ${result.filename}`;
                    // link.download = result.filename; // handled by Content-Disposition usually
                    downloadLinks.appendChild(link);
                } else {
                    const errorMsg = document.createElement('div');
                    errorMsg.style.color = 'var(--error)';
                    errorMsg.textContent = `Error processing ${result.filename}: ${result.error}`;
                    downloadLinks.appendChild(errorMsg);
                }
            });

            statusMessage.textContent = 'Processing complete.';

        } catch (error) {
            console.error(error);
            statusMessage.textContent = 'An error occurred during injection.';
        } finally {
            injectBtn.disabled = false;
            injectBtn.textContent = 'Inject Metadata';
        }
    });
});
