# FROM python:3.12.9-bookworm
# ARG JULIA_RELEASE=1.10
# ARG JULIA_VERSION=1.10.0
# FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04
FROM pytorch/pytorch:2.6.0-cuda11.8-cudnn9-devel

ARG JULIA_RELEASE=1.11
ARG JULIA_VERSION=1.11.4
# ARG JULIA_VERSION=1.9.0-rc3

ENV DEBIAN_FRONTEND=noninteractive




# julia

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install --yes --no-install-recommends \
    # basic stuff
    curl ca-certificates nano && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


# RUN apt-get update && \
#     apt-get install -y software-properties-common && \
#     add-apt-repository ppa:deadsnakes/ppa && \
#     apt-get update && \
#     apt-get install -y python3.11 python3.11-venv python3.11-dev && \
#     update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1



RUN curl -s -L https://julialang-s3.julialang.org/bin/linux/x64/${JULIA_RELEASE}/julia-${JULIA_VERSION}-linux-x86_64.tar.gz | \
    tar -C /usr/local -x -z --strip-components=1 -f -



RUN apt-get update -q -y && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install -q -y --allow-change-held-packages\
    vim net-tools curl \
    libgl1-mesa-glx \
    xserver-xorg-video-dummy \
    libxrender1 \
    libpulse0 \
    libpulse-mainloop-glib0  \
    libnss3  \
    libxcomposite1 \
    libfontconfig1 \
    libxrandr2 \
    libasound2 \
    libglu1 \
    x11vnc \
    awesome \
    jq \
    nautilus\
    jupyter-core\
    # zip\
    # p7zip-full\
    # apt-utils\
    # octave\
    kmod\
    zlib1g\
    bzip2\
    cmake\
    libfreetype6-dev \
    curl\
    git \
    cmake \
    g++ \
    libssl-dev \  
    pkg-config \  
    gcc 

    # RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    #     python3 get-pip.py && \
    #     rm get-pip.py
# RUN python3 -m pip  --no-cache-dir install install --no-cache-dir monai

RUN apt-get install --yes --no-install-recommends wget build-essential libcurl4 && \
    wget https://curl.se/download/curl-7.81.0.tar.gz && \
    tar -xvf curl-7.81.0.tar.gz && cd curl-7.81.0 && \
    ./configure --with-openssl && make && make install

# RUN NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
#     # pip install pygraphviz
# RUN test -d ~/.linuxbrew && eval "$(~/.linuxbrew/bin/brew shellenv)"
# RUN test -d /home/linuxbrew/.linuxbrew && eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
# RUN echo "eval \"\$($(brew --prefix)/bin/brew shellenv)\"" >> ~/.bashrc
# RUN apt-get update && apt-get install -y graphviz graphviz-dev



RUN python3 -m  pip install \
    SimpleITK\
    numpy\
    tensorboard-plugin-profile \
    tensorboard \
    pandas \
    einops \
    jupyter \
    scikit-learn \
    stepmix \
    seaborn \
    matplotlib \
    optuna \
    pgmpy \
    networkx \
    daft \ 
    sweetviz \
    requests \
aiohttp \
streamlit \
nest_asyncio \
langchain \
ollama \
chromadb \
langchain_community \
pydantic \
transformers \
kg-gen \
streamlit-lottie \
vtk \
ipywidgets \
    requests \
    glob2 \
    pytest-shutil \
    pydicom \
    torch torchvision torchaudio \
    accelerate
    
RUN python3 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
RUN python3 -m pip install faiss-gpu-cu11 bitsandbytes







RUN set -ex \
    && RUN_DEPS=" \
    build-essential \
    tk-dev \
    mesa-common-dev \
    wget \
    " \
    && seq 1 8 | xargs -I{} mkdir -p /usr/share/man/man{} \
    && apt-get update && apt-get install -y --no-install-recommends $RUN_DEPS \
    && rm -rf /var/lib/apt/lists/*

RUN \
    wget \
    -O sqlite.tar.gz \
    https://www.sqlite.org/src/tarball/sqlite.tar.gz?r=release \
    && \
    tar xvfz sqlite.tar.gz

RUN \
    ./sqlite/configure --prefix=/usr && \
    make && \
    make install \
    && \
    # Smoke test
    sqlite3 --version


