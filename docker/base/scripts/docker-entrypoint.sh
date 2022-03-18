#!/bin/bash

set -ex

exec gosu reviewbot "$@"
