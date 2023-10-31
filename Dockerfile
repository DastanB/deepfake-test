FROM nvidia/cuda:12.2.0-base-ubuntu20.04

ENV DEBIAN_FRONTEND noninteractive
ENV DJANGO_ENV=production
ENV DEEPFAKE_DB_NAME=DeepFake
ENV DEEPFAKE_DB_USER=DeepFake
ENV DEEPFAKE_DB_PASSWORD=dHBDj|k8+v~Ie/.?
ENV DEEPFAKE_DB_HOST=35.233.55.115
ENV DEEPFAKE_DB_PORT=5432

RUN apt-get update -y

# fix nvidia public key
RUN apt-key del 7fa2af80
RUN apt install -y wget
RUN apt-key adv --fetch-keys http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/3bf863cc.pub

RUN apt install -y \
	curl \
	wget \
	git \
	make \
	automake \
	gcc \
	g++ \
	subversion \
	python3-dev \
    python3-pip \
	cmake \
	pkg-config \
	libx11-dev \
	libatlas-base-dev \
	libgtk-3-dev \
	libboost-python-dev -y

# copy relevant files
COPY ./ /app/
COPY ./requirements.txt /app/requirements.txt

# switch working directory
WORKDIR /app

# install the dependencies and packages in the requirements file
RUN pip3 install --upgrade pip
RUN pip3 install torch==2.0.1

RUN BASICSR_EXT=True pip3 install basicsr
RUN pip3 install -r requirements.txt
RUN pip3 install cmake pip install onnxruntime-gpu

# configure the container to run in an executed manner
ENTRYPOINT [ "python" ]

CMD ["manage.py", "runserver"]
