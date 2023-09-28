#!/bin/bash

dd if=/dev/urandom bs=1M count=10 | curl -X POST http://localhost:8000 --data-binary "@-" -H "Transfer-Encoding: chunked"

