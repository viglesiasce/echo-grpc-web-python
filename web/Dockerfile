FROM ubuntu:16.04

ARG MAKEFLAGS=-j8

RUN apt-get update && apt-get install -y \
  autoconf \
  automake \
  build-essential \
  curl \
  git \
  default-jdk \
  default-jre \
  libtool \
  libpcre3-dev \
  libssl-dev \
  make \
  nginx \
  zip

RUN curl -sL https://deb.nodesource.com/setup_8.x | bash - && \
  apt-get install -y nodejs

COPY grpc-web/ /src/grpc-web/

RUN cd /src/grpc-web/third_party/grpc && \
  make && make install

RUN cd /src/grpc-web/third_party/grpc/third_party/protobuf && \
  make install

RUN cd /src/grpc-web/javascript/net/grpc/web && \
  make

RUN cd /src/grpc-web && make plugin

RUN mkdir /src/echo

WORKDIR  /src/echo/web

COPY web/package.json .
RUN npm install

COPY protos/echo.proto ./web/* ./

RUN protoc -I=. echo.proto \
  --plugin=protoc-gen-grpc-web=/src/grpc-web/javascript/net/grpc/web/protoc-gen-grpc-web \
  --grpc-web_out=import_style=commonjs,mode=grpcwebtext,out=echo_grpc_pb.js:. \
  --js_out=import_style=commonjs:.

RUN npm link grpc-web && npx webpack

FROM nginx:stable
COPY --from=0 /src/echo/web/ /usr/share/nginx/html/
