##############################################################################
# Install App
##############################################################################
FROM python:3.14.0a2-alpine3.20
WORKDIR /spatialmediatools/app
ENV PATH="${PATH}:/spatialmediatools/app"

RUN apk update && \
    apk upgrade && \
    apk --no-cache add --virtual wget unzip ca-certificates 

COPY ./requirements.txt /spatialmediatools/app/requirements.txt
RUN python -m venv spatialmediatools 
RUN source spatialmediatools/bin/activate
RUN spatialmediatools/bin/python -m pip install --upgrade pip
RUN spatialmediatools/bin/python -m pip install -r requirements.txt
RUN spatialmediatools/bin/python -m pip install -I gunicorn

COPY ./app.py /spatialmediatools/app
COPY ./wsgi.py /spatialmediatools/app
COPY ./startup.sh /spatialmediatools/app 
RUN chmod 777 /spatialmediatools/app/startup.sh
RUN mkdir ./data

##############################################################################
# Download and extract Spatial Metadata Tools Code
##############################################################################
ENV GIT_URL="https://github.com/google/spatial-media/archive/refs/heads/master.zip"
ENV APP_DIR="/spatialmediatools/app"

RUN wget --no-check-certificate -O spatialmediatools.zip $GIT_URL;
RUN unzip $APP_DIR/spatialmediatools.zip;

##############################################################################
# Clean up of unneeded packages and download
##############################################################################
RUN rm -rf /var/cache/apk/*;
RUN rm $APP_DIR/spatialmediatools.zip 
RUN apk del wget unzip ca-certificates;

##############################################################################
# Run app.py
##############################################################################
#CMD [ "spatialmediatools/bin/python", "app.py" ]
ENTRYPOINT [ "/spatialmediatools/app/startup.sh" ]
