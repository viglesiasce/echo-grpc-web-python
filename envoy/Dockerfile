FROM envoyproxy/envoy:latest

COPY envoy/envoy.yaml /etc/envoy/envoy.yaml

CMD /usr/local/bin/envoy -c /etc/envoy/envoy.yaml -l trace