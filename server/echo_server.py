from concurrent import futures
import time
import logging

import grpc

import echo_pb2
import echo_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


class Echo(echo_pb2_grpc.EchoServiceServicer):

    def Echo(self, request, context):
        logging.debug("Processing Echo: " + str(request))
        return echo_pb2.EchoResponse(message=request.message)
    
    def EchoAbort(self, request, context):
        logging.debug("Processing Abort: " + str(request))
        context.set_code(grpc.StatusCode.ABORTED)
        return echo_pb2.EchoResponse(message=request.message)
    
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
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()