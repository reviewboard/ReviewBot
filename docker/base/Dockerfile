# Dockerfile for Review Bot.
#
# Copyright (C) 2022 Beanbag, Inc.


##############################################################################
# Stage 1 of the build.
#
# We'll set up some common environment variables we'll want in subsequent
# stages.
#
# We're using Ubuntu (LTS release), due to the longer support life.
##############################################################################
FROM ubuntu:22.04 AS base

# Set up the environment for Python, NPM, Ruby, and scripts.
ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$NPM_CONFIG_PREFIX/bin:$PATH"
ENV GEM_HOME=/opt/ruby/gems
ENV NPM_CONFIG_PREFIX=/opt/nodejs/node_modules
ENV RUSTUP_HOME=/opt/rust/rustup
ENV CARGO_HOME=/opt/rust/cargo
ENV PATH="$VIRTUAL_ENV/bin:$NPM_CONFIG_PREFIX/bin:$GEM_HOME/bin:$CARGO_HOME/bin:$PATH"


##############################################################################
# Stage 2 of the build.
#
# We'll set up development support and compile any modules we need in a
# virtualenv. That will be copied in stage 2 to the destination image, without
# carrying all the development bloat.
#
##############################################################################
FROM base AS builder
MAINTAINER Beanbag, Inc. <support@beanbaginc.com>

# The version of Review Bot this will install.
ARG REVIEWBOT_VERSION=3.0a0

# Install all the base system-level packages needed by Review Bot.
#
# We will be installing some packages (including most Python packages) via
# pip instead of apt-get.
RUN    set -ex \
    && apt-get update -y \
    && apt-get upgrade -y \
    && DEBIAN_FRONTEND="noninteractive" apt-get install \
           -y --no-install-recommends \
           ca-certificates \
           curl \
           software-properties-common \
           virtualenv \
    && rm -rf /var/lib/apt/lists/*

RUN virtualenv -p python3 $VIRTUAL_ENV

# Install Review Bot and its Python dependencies.
#
# If any packages are provided in ./packages/ when building this, we'll
# prioritize those.
COPY ./packages /tmp/packages
RUN    set -ex \
    && pip3 install -U pip \
    && pip3 install \
           --no-cache-dir \
           --pre \
           --find-links /tmp/packages \
           reviewbot-worker~=${REVIEWBOT_VERSION} \
    && rm -rf /tmp/packages

COPY scripts/* /opt/scripts/
COPY files/reviewbot-config.py /etc/xdg/reviewbot/config.py


##############################################################################
# Stage 2 of the build.
#
# We'll create a new, final image that contains the virtualenv and only the
# runtime dependencies necessary to run Review Bot.
##############################################################################
FROM base AS standalone

# Review Bot user ID
#
# Review Bot will run as this user, and writable directories (/repos/) will be
# owned by this user.
ARG REVIEWBOT_USER_ID=1001

# Review Bot group ID
#
# Writable directories (/repos) will be owned by this group.
ARG REVIEWBOT_GROUP_ID=1001

# The broker URL to connect to.
#
# This is required.
ENV BROKER_URL=amqp://reviewbot:reviewbot123@rabbitmq/reviewbot

# Log level for Review Bot.
ENV LOG_LEVEL=INFO

# Number of workers to run concurrently.
#
# If blank, this will be based on the number of CPUs on the system.
ENV NUM_WORKERS=

# Location of the configuration file.
#
# Mount this somewhere and configure a config.py.
VOLUME /config

# Location of the repository checkouts directory.
#
# Mount this somewhere to share any repository checkouts across containers.
VOLUME /repos


# Create a user for the web server and set up symlinks for the repositories
# directory.
RUN    groupadd -r reviewbot -g $REVIEWBOT_GROUP_ID \
    && adduser --system --uid $REVIEWBOT_USER_ID \
               --disabled-password --disabled-login \
               --ingroup reviewbot reviewbot \
    && mkdir -p /usr/local/share/reviewbot \
    && ln -s /repos /usr/local/share/reviewbot/repositories

RUN    apt-get update -y \
    && DEBIAN_FRONTEND="noninteractive" apt-get install \
           -y --no-install-recommends \
           ca-certificates \
           curl \
           git \
           gosu \
           patch \
           python3 \
           python3-distutils \
    && rm -rf /var/lib/apt/lists/*

# Copy results from the previous builder.
COPY --from=builder /etc/apt /etc/apt
COPY --from=builder /etc/xdg/reviewbot /etc/xdg/reviewbot
COPY --from=builder /opt /opt

# Install the space-delimited list of tools needed in the derived image.
#
# There's some light customization allowed here. Users have control over
# a couple of the versions. Most things will just use the latest available
# versions from the appropriate package repositories, though.
#
# Long-term, it would be nice to allow for specifying explicit versions in
# the TOOLS list, where possible.
ONBUILD ARG FBINFER_VERSION=1.1.0
ONBUILD ARG PMD_VERSION=6.43.0
ONBUILD ARG TOOLS
ONBUILD RUN /opt/scripts/install-tools.sh ${TOOLS}

# Periodically check that the worker is up and responding.
HEALTHCHECK CMD /opt/scripts/docker-healthcheck.sh

# Run the Review Bot worker.
ENTRYPOINT ["/opt/scripts/docker-entrypoint.sh"]
CMD ["/opt/scripts/run-reviewbot.sh"]
