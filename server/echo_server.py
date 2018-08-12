from concurrent import futures
import time
import logging

import grpc
from prometheus_client import start_http_server, Summary

import echo_pb2
import echo_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

# Create a metric to track time spent and requests made.
ECHO_REQUEST_TIME = Summary('echo_request_processing_seconds', 'Time spent processing Echo request')
STREAMING_ECHO_REQUEST_TIME = Summary('streaming_echo_request_processing_seconds', 'Time spent processing StreamingEcho request')

class Echo(echo_pb2_grpc.EchoServiceServicer):

    @ECHO_REQUEST_TIME.time()
    def Echo(self, request, context):
        logging.debug("Processing Echo: " + str(request))
        return echo_pb2.EchoResponse(message=request.message)
    
    def EchoAbort(self, request, context):
        logging.debug("Processing Abort: " + str(request))
        context.set_code(grpc.StatusCode.ABORTED)
        return echo_pb2.EchoResponse(message=request.message)
    
    @STREAMING_ECHO_REQUEST_TIME.time()
    def ServerStreamingEcho(self, request, context):
        logging.debug("Processing ServerStreamingEcho: " + str(request))
        for _ in range(request.message_count):
            time.sleep(request.message_interval/1000)
            yield echo_pb2.EchoResponse(message=request.message)


def serve():
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
    port = 50051
    logging.info("Starting server on port %d" % port)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    echo_pb2_grpc.add_EchoServiceServicer_to_server(Echo(), server)
    
    server.add_insecure_port('[::]:' + str(port))
    server.start()
    start_http_server(9090)

    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()