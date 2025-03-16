FROM alpine:3.20
COPY ./ping-test/ping.sh /ping.sh
RUN chmod +x /ping.sh
ENTRYPOINT ["/bin/sh", "/ping.sh"]