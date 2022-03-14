#!/bin/bash

celery -b $BROKER_URL inspect ping celery@$HOSTNAME
