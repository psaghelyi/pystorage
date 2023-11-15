#!/bin/bash

# Function to execute upon signal catch
cleanup() {
    echo "Caught Ctrl+C, cleaning up and exiting."
    rm content.bin
    exit
}

# Trap SIGINT (Ctrl+C) signal
trap cleanup SIGINT

dd if=/dev/urandom of=content.bin bs=1M count=10

while true
do
    curl -X PUT http://192.168.1.105:8000 --data-binary "@content.bin" -H "Transfer-Encoding: chunked"
done
