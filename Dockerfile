FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04
WORKDIR /app
COPY app.py /app
COPY lib /app/lib
COPY templates /app/templates

COPY requirements.txt /app
RUN apt-get update &&  \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    python3.11 \
    python3-pip \
    python3-setuptools \
    python3-dev \
    build-essential \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Install FFmpeg
RUN apt update && \
    DEBIAN_FRONTEND=noninteractive apt install -y software-properties-common && \
    add-apt-repository universe && \
    DEBIAN_FRONTEND=noninteractive apt install -y ffmpeg

CMD ["gunicorn", "-b", "0.0.0.0:9912", "-t", "300", "app:app"]