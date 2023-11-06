#!/bin/bash

echo "users: ${NUM_USERS}"

locust --master --headless \
-f locustfile.py \
--host http://frontend:8080 \
-u $NUM_USERS \
-r $SPAWN_RATE \
--run-time $RUN_TIME \
--csv $CSV_FILENAME \
--expect-workers $NUM_WORKERS

