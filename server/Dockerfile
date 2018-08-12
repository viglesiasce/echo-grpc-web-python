FROM python:2
WORKDIR /usr/src/app
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY protos/echo.proto ./
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. echo.proto
COPY server/*.py ./
CMD [ "python", "echo_server.py" ]