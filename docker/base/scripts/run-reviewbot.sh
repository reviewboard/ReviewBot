#!/bin/bash

set -ex

CONCURRENCY_ARGS=

if test ! -z "$NUM_WORKERS"; then
    CONCURRENCY_ARGS="-c $NUM_WORKERS"
fi

/usr/bin/env reviewbot -b $BROKER_URL -l$LOG_LEVEL $CONCURRENCY_ARGS
