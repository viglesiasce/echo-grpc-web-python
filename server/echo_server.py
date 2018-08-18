import logging
import time
import datetime
from concurrent import futures

import grpc
import prometheus_client
from opencensus.trace.exporters import zipkin_exporter
from opencensus.trace.ext.grpc import server_interceptor
from opencensus.trace.samplers import always_on
from opencensus.trace.span_context import SpanContext
from opencensus.trace.tracer import Tracer
from opencensus.trace.time_event import TimeEvent, Annotation
from opencensus.trace.tracers.context_tracer import ContextTracer
from prometheus_client import Summary

import echo_pb2
import echo_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

# Create a metric to track time spent and requests made.
ECHO_REQUEST_TIME = Summary('echo_request_processing_seconds', 'Time spent processing Echo request') 
STREAMING_ECHO_REQUEST_TIME = Summary('streaming_echo_request_processing_seconds', 'Time spent processing StreamingEcho request')

sampler = always_on.AlwaysOnSampler()
exporter = zipkin_exporter.ZipkinExporter(service_name="server:50051", host_name="zipkin")


def GetTracingMetadata(context):
    metadata_tuples = context.invocation_metadata()
    metadata_dict = {}
    metadata_list = []
    for i in range(len(metadata_tuples)):
        metadatum = metadata_tuples[i]
        logging.debug("Checking metadatum: " + metadatum.key)
        if metadatum.key in ['x-request-id', 'x-b3-traceid', 'x-b3-spanid', 'x-b3-parentspanid', 'x-b3-sampled', 'x-b3-flags', 'x-ot-span-context']:
            metadata_dict[metadatum.key] = metadatum.value
            logging.debug("Adding metadata headers to echo: " + str(metadatum))
            metadata_list.append(metadata_tuples[i])
    #context.set_trailing_metadata(tuple(metadata_list))
    logging.debug("Metadata list: " + str(metadata_list))
    return metadata_dict       

class Echo(echo_pb2_grpc.EchoServiceServicer):

    @ECHO_REQUEST_TIME.time()
    def Echo(self, request, context):
        metadata = context.invocation_metadata()
        logging.debug("Echo metadata: " + str(metadata))
        metadata_dict = GetTracingMetadata(context)
        logging.debug("Metadata dict: " + str(metadata_dict))
        
        if 'x-b3-traceid' in metadata_dict:
            trace_id = metadata_dict['x-b3-traceid']
            logging.debug("Trace ID: " + trace_id)
            span_context = SpanContext(trace_id=trace_id, span_id=metadata_dict['x-b3-spanid'])
            tracer = Tracer(span_context=span_context, exporter=exporter, sampler=always_on.AlwaysOnSampler())
            with tracer.span(name='echo') as span:
                logging.debug("Processing Echo: " + str(request))
                span.add_attribute("message", request.message)
                time.sleep(0.2)
                with tracer.span(name='echo-inner') as inner:
                    inner.add_attribute("delay", "0.2")
                    time.sleep(0.2)
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
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),)
        #interceptors=(tracer_interceptor,))
    echo_pb2_grpc.add_EchoServiceServicer_to_server(Echo(), server)
    
    server.add_insecure_port('[::]:' + str(port))
    server.start()
    prometheus_client.start_http_server(9090)

    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
