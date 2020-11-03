![CI](https://github.com/libanvl/python-protoflux/workflows/CI/badge.svg)

# python-protoflux
Forge-weld [betterproto](https://github.com/danielgtaylor/python-betterproto) and [grpclib](https://github.com/vmagamedov/grpclib) for modern protobuf message implementations over async servers. 

Based heavily on the work of [w4rum](https://gist.github.com/w4rum/4e20ec18b9065b1b6780e2f92ac4b6f0)
and [nat-n](https://gist.github.com/nat-n/e90097ebfb861cbb25e20b68bec0e39c)

# Usage (for an async gRpc server)

1. Create your .proto files
2. Use betterproto to generate the message files:
  protoc: `protoc -I . --python_betterproto_out=lib example.proto`
3. Create your server class
  * decorate the class with @grpc_server("package.ServiceName")
  * decorate each handler method with @grpc_handler
  * override default handler names (snake_case -> TitleCase) with @grpc_name
4. Pass an instance of the server to grpclib.Server and start the server

# Developing

## Install pipx if pipenv is not installed
python3 -m pip install pipx
python3 -m pipx ensurepath

## Install pipenv using pipx
pipx install pipenv

## Init
./init.sh
