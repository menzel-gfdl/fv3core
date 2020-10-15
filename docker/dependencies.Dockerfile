ARG BASE_IMAGE=ubuntu:19.10

ARG MIDBASE=fv3core-install-serialbox
FROM $BASE_IMAGE as fv3core-install-base

###
### Install some prerequisite system packages
###
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gcc g++ make libtool m4 \
    libpython3-dev python3-numpy python3-scipy python3-pip \
    cmake \
    libnetcdf-dev libnetcdff-dev \
    libssl-dev \
    git && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3 10 && \
    update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 10 && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get purge --auto-remove && \
    apt-get clean

###
### Build and install Boost Libraries
###
# RUN tar xzf boost_1_73_0.tar.gz && \
#    cd boost_1_73_0 && ./bootstrap.sh --prefix=/usr && \
#    ./b2 stage -j4 threading=multi link=shared && \
#    ./b2 install threading=multi link=shared && \
#    ln -svf detail/sha1.hpp /usr/include/boost/uuid/sha1.hpp && \
#    cd .. && rm boost_1_73_0.tar.gz
RUN wget -q https://dl.bintray.com/boostorg/release/1.73.0/source/boost_1_73_0.tar.gz && \
    tar -xzf boost_1_73_0.tar.gz -C /usr/local && \
    (cd /usr/local/boost_1_73_0 && cp -r boost /usr/local/include/) && \
    rm -rf boost_1_73_0.tar.gz /usr/local/boost_1_73_0

FROM fv3core-install-base as fv3core-install-serialbox

###
### Build and install Serialbox
###
RUN git clone -b v2.6.0 --depth 1 https://github.com/GridTools/serialbox.git /usr/src/serialbox && \
    cmake -B build -S /usr/src/serialbox -DSERIALBOX_USE_NETCDF=ON -DSERIALBOX_TESTING=ON \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local && \
    cmake --build build/ -j $(nproc) --target install && \
    rm -rf build /usr/src/serialbox

FROM $MIDBASE as fv3core-install

###
### Install fv3core requirements
###

# First, upgrade pip and install requirements for the build system and extras
RUN pip install --no-cache-dir --upgrade pip setuptools wheel tox cupy-cuda102==7.7.0

# Copy pinned requirements file
COPY requirements_hpc.txt requirements_hpc.txt
RUN pip install --no-cache-dir --use-feature=2020-resolver -r requirements_hpc.txt

###
### Build and install GT4Py
###
ENV BOOST_HOME=/usr/local/boost_1_73_0
ARG CPPFLAGS="-I${BOOST_HOME} -I${BOOST_HOME}/boost"
RUN pip install --no-cache-dir --use-feature=2020-resolver git+https://github.com/VulcanClimateModeling/gt4py.git@develop#egg=gt4py[cuda102] && \
    python -m gt4py.gt_src_manager install
