##############################################################################
# Install App
##############################################################################
FROM python:3.14.0a2-alpine3.20
WORKDIR /spatialmediatools/app
ENV PATH="${PATH}:/spatialmediatools/app"

RUN apk update && \
    apk upgrade && \
    apk --no-cache add --virtual build-dependencies wget unzip ca-certificates 

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install dependencies
COPY ./requirements.txt /spatialmediatools/app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Create startup script
RUN echo '#!/bin/sh' > /spatialmediatools/app/startup.sh && \
    echo 'mkdir -p /spatialmediatools/app/data' >> /spatialmediatools/app/startup.sh && \
    echo 'exec tail -f /dev/null' >> /spatialmediatools/app/startup.sh && \
    chmod +x /spatialmediatools/app/startup.sh

##############################################################################
# Download and extract Spatial Metadata Tools Code
##############################################################################
ENV GIT_URL="https://github.com/google/spatial-media/archive/refs/heads/master.zip"
ENV APP_DIR="/spatialmediatools/app"

RUN wget --no-check-certificate -O spatialmediatools.zip $GIT_URL && \
    unzip $APP_DIR/spatialmediatools.zip && \
    rm $APP_DIR/spatialmediatools.zip

##############################################################################
# Clean up of unneeded packages and download
##############################################################################
RUN rm -rf /var/cache/apk/* && \
    apk del wget unzip ca-certificates

##############################################################################
# Set up entry point
##############################################################################
COPY ./app.py /spatialmediatools/app
COPY ./wsgi.py /spatialmediatools/app

# Ensure data directory exists
RUN mkdir -p /spatialmediatools/app/data

# Use the startup script as entrypoint
ENTRYPOINT ["/spatialmediatools/app/startup.sh"]