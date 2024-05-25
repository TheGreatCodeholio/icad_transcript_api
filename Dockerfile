FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

LABEL maintainer="ian@icarey.net"

ARG USER_ID=9911
ARG GROUP_ID=9911

RUN addgroup --gid ${GROUP_ID} icad && \
    adduser --uid ${USER_ID} --gid ${GROUP_ID} icad

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /usr/src/app
COPY app.py /app
COPY lib /app/lib
# COPY static /app/static
COPY templates /app/templates
COPY requirements.txt /app

# Update Packages List and Install requirements
RUN apt update  && \
    DEBIAN_FRONTEND=noninteractive apt install -y software-properties-common && \
    add-apt-repository universe && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-distutils \
    python3.11-venv \
    python3-pip \
    python3-setuptools \
    python3-dev \
    build-essential \
    libmagic1 \
    tzdata \
    ffmpeg \
    libcudnn8 \
    libcudnn8-dev \
    && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

RUN apt remove python3-blinker -y

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Set the timezone (example: America/New_York)
ENV TZ=America/New_York

# Upgrade pip
RUN pip3 install --upgrade pip

# Install any needed packages specified in requirements.txt
RUN pip3 install -r requirements.txt

USER icad

CMD ["gunicorn", "-b", "0.0.0.0:9912", "-t", "300", "app:app"]