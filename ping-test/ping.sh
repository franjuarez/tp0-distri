#!/bin/bash

SERVER_IP=server
SERVER_PORT=12345

MESSAGE="Hola server!"

RESPONSE=$(echo $MESSAGE | nc $SERVER_IP $SERVER_PORT)

RESULT=fail

if [ "$RESPONSE" == "$MESSAGE" ]; then
    RESULT=success
fi

echo "action: test_echo_server | result: $RESULT"