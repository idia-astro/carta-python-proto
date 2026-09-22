CARTA Python Frontend/Backend Interface
---------------------------------------

A bare-bones Python library for communicating with the CARTA backend using the protocol buffer messages defined in the frontend/backend ICD and found in `carta-protobuf`. Under construction. Intended for simple interactive tests; may be useful for extracting data from the backend or profiling backend behaviour.

(Not to be confused with `carta-python`, which is a wrapper for scripting CARTA by communicating with the frontend via a HTTP interface in the backend.)

You can install this by running `pip install .` (with an appropriate version of `pip`) in the top-level directory (after checking out the `carta-protobuf` submodule). This will automatically generate and install the protocol buffer message objects in the `cartaproto.proto` submodule. `cartaproto.messages` and `cartaproto.enums` are more user-friendly interfaces to these generated objects. `cartaproto.client.Client` is a simple client implementation.

Example scripts go in `examples`.
