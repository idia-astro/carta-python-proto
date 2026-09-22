from google.protobuf.symbol_database import Default
from . import proto

factory = Default()
messages = dict()

for cp_key, cp_val in proto.__dict__.items():
    if cp_key.endswith("_pb2"):
        for msg_name in cp_val.DESCRIPTOR.message_types_by_name.keys():
            messages[msg_name] = getattr(cp_val, msg_name)

del factory, cp_key, cp_val, msg_name
globals().update(messages)
