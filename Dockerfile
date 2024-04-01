FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04
WORKDIR /app
COPY app.py /app
COPY lib /app/lib
COPY templates /app/templates
COPY static /app/static

COPY requirements.txt /app
RUN apt update &&  \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    python3-pip \
    python3-setuptools \
    python3-dev \
    build-essential \
    && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip3 install --upgrade pip

# Install any needed packages specified in requirements.txt
RUN pip3 install -r requirements.txt

# Install FFmpeg
RUN apt update && \
    DEBIAN_FRONTEND=noninteractive apt install -y software-properties-common && \
    add-apt-repository universe && \
    DEBIAN_FRONTEND=noninteractive apt install -y ffmpeg

CMD ["gunicorn", "-b", "0.0.0.0:9912", "-t", "300", "app:app"]