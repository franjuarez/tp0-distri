#!/bin/bash
sudo docker build -f ping-test/Dockerfile -t ping-test .
sudo docker run --network testing_net ping-test:latest