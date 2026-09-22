from . import proto

enums = dict()

for cp_key, cp_val in proto.__dict__.items():
    if cp_key.endswith("_pb2"):
        for enum_name in cp_val.DESCRIPTOR.enum_types_by_name.keys():
            enums[enum_name] = getattr(cp_val, enum_name)

del cp_key, cp_val, enum_name
globals().update(enums)
