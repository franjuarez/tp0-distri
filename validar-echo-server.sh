#!/bin/bash
docker build -f ping-test/Dockerfile -t ping-test .
docker run --network tp0_testing_net ping-test:latest

docker stop ping-test
docker rm ping-test