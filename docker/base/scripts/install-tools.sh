#!/bin/bash
#
# Install packages needed for tools.
#
# Some notes on pattern matching: The reason we have patterns, rather than
# putting these inline in the if statements, is due to our need to use
# whitespace to separate tool names, and bash's inability to match regexes
# inline when they contain whitespace (quotes will escape everything within).

set -e

apt_packages=()
apt_temp_packages=()
py_packages=()
npm_packages=()
gem_packages=()
rustup_packages=()

ALL_TOOLS=" $@ "


export DEBIAN_FRONTEND="noninteractive"


# C-based tools
TOOL_CLANG=' clang '
TOOL_CPPCHECK=' cppcheck '
TOOL_CPPLINT=' cpplint '

if [[ $ALL_TOOLS =~ $TOOL_CLANG ]]; then
    apt_packages+=("clang" "clang-tools")
fi

if [[ $ALL_TOOLS =~ $TOOL_CPPCHECK ]]; then
    apt_packages+=("cppcheck")
fi

if [[ $ALL_TOOLS =~ $TOOL_CPPLINT ]]; then
    py_packages+=("cpplint")
fi


# Go
TOOL_GO_ALL=' go(fmt|test) '

if [[ $ALL_TOOLS =~ $TOOL_GO_ALL ]]; then
    apt_packages+=("golang-go")
fi


# Java
TOOL_CHECKSTYLE=' checkstyle '

if [[ $ALL_TOOLS =~ $TOOL_CHECKSTYLE ]]; then
    apt_packages+=("checkstyle")
fi


# JavaScript
TOOL_JSHINT=' jshint '
TOOL_NPM_ALL=" (jshint) "

if [[ $ALL_TOOLS =~ $TOOL_NPM_ALL ]]; then
    apt_packages+=("nodejs" "npm")
fi

if [[ $ALL_TOOLS =~ $TOOL_JSHINT ]]; then
    apt_packages+=("nodejs" "npm")
    npm_packages+=("jshint")
fi


# Python
TOOL_DOC8=' doc8 '
TOOL_FLAKE8=' flake8 '
TOOL_PYCODESTYLE=' pycodestyle '
TOOL_PYDOCSTYLE=' pydocstyle '
TOOL_PYFLAKES=' pyflakes '

if [[ $ALL_TOOLS =~ $TOOL_DOC8 ]]; then
    py_packages+=("doc8")
fi

if [[ $ALL_TOOLS =~ $TOOL_FLAKE8 ]]; then
    py_packages+=("flake8")
fi

if [[ $ALL_TOOLS =~ $TOOL_PYCODESTYLE ]]; then
    py_packages+=("pycodestyle")
fi

if [[ $ALL_TOOLS =~ $TOOL_PYDOCSTYLE ]]; then
    py_packages+=("pydocstyle")
fi

if [[ $ALL_TOOLS =~ $TOOL_PYFLAKES ]]; then
    py_packages+=("pyflakes")
fi


# Ruby
TOOL_RUBOCOP=' rubocop '
TOOL_RUBY_ALL=' (rubocop) '

if [[ $ALL_TOOLS =~ $TOOL_RUBY_ALL ]]; then
    apt_packages+=("ruby")
fi

if [[ $ALL_TOOLS =~ " rubocop " ]]; then
    gem_packages+=("rubocop")
fi


# Rust
TOOL_RUSTFMT=' rustfmt '
TOOL_RUST_ALL=' (rustfmt) '

if [[ $ALL_TOOLS =~ $TOOL_RUST_ALL ]]; then
    curl https://sh.rustup.rs -sSf | sh -s -- -y --profile=minimal
fi

if [[ $ALL_TOOLS =~ $TOOL_RUSTFMT ]]; then
    rustup_packages+=("rustfmt")
fi


# Shell
TOOL_SHELLCHECK=' shellcheck '

if [[ $ALL_TOOLS =~ $TOOL_SHELLCHECK ]]; then
    apt_packages+=("shellcheck")
fi

# Now for the more complex, standalone tools.

# FBInfer
TOOL_FBINFER=' fbinfer '

if [[ $ALL_TOOLS =~ $TOOL_FBINFER ]]; then
    apt_temp_packages+=("xz-utils")

    apt-get update -y
    apt-get install -y xz-utils

    curl -sSL \
        https://github.com/facebook/infer/releases/download/v${FBINFER_VERSION}/infer-linux64-v${FBINFER_VERSION}.tar.xz \
        | tar -xJ -C /opt
    mv /opt/infer-linux64-v${FBINFER_VERSION} /opt/fbinfer
    chown -R root:root /opt/fbinfer
fi


# PMD
TOOL_PMD=' pmd '

if [[ $ALL_TOOLS =~ $TOOL_PMD ]]; then
    apt_packages+=("default-jre-headless")
    apt_temp_packages+=("unzip")

    apt-get update -y
    apt-get install -y unzip

    curl -sSL -o /tmp/pmd.zip \
        https://github.com/pmd/pmd/releases/download/pmd_releases%2F${PMD_VERSION}/pmd-bin-${PMD_VERSION}.zip
    unzip -d /opt /tmp/pmd.zip
    rm /tmp/pmd.zip
    mv /opt/pmd-bin-${PMD_VERSION} /opt/pmd
fi


# Install the collected packages.
if [[ "${#apt_packages[@]}" -gt 0 ]]; then
    apt-get update -y
    apt-get install -y --no-install-recommends ${apt_packages[*]}
    apt-get clean -y
    rm -rf /var/lib/apt/lists/* /var/apt/cache/*
fi

if [[ "${#py_packages[@]}" -gt 0 ]]; then
    pip3 install --no-cache-dir ${py_packages[@]}
fi

if [[ "${#npm_packages[@]}" -gt 0 ]]; then
    npm install -g ${npm_packages[@]}
fi

if [[ "${#gem_packages[@]}" -gt 0 ]]; then
    gem install --no-document ${gem_packages[@]}
fi

if [[ "${#rustup_packages[@]}" -gt 0 ]]; then
    rustup component add ${rustup_packages[@]}
fi

# Remove anything we no longer need.
if [[ "${#apt_temp_packages[@]}" -gt 0 ]]; then
    apt-get remove -y ${apt_temp_packages[@]}
fi
