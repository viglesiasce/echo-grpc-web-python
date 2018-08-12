from __future__ import print_function

import grpc

import echo_pb2
import echo_pb2_grpc


def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = echo_pb2_grpc.EchoServiceStub(channel)
        response = stub.Echo(echo_pb2.EchoRequest(message='you'))
    print("Client received: " + response.message)


if __name__ == '__main__':
    run()
