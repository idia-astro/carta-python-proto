import asyncio
import struct
import uuid

import numpy as np
import websockets

from .messages import messages, RegisterViewer
from .enums import EventType
from .proto import MAJOR_VERSION


class Client:
    @classmethod
    def init_event_maps(cls):
        cls.EVENT_TYPE_TO_MSG_CLASS = dict()

        for event_name, event_type in EventType.items():
            class_name = event_name.title().replace("_", "")
            try:
                cls.EVENT_TYPE_TO_MSG_CLASS[event_type] = messages[class_name]
            except KeyError:
                if event_name == "EMPTY_EVENT":
                    continue # this is a dummy value
                if event_name == "FILE_LIST_PROGRESS":
                    # We should fix this name
                    cls.EVENT_TYPE_TO_MSG_CLASS[EventType.FILE_LIST_PROGRESS] = messages["ListProgress"]
                    continue
                raise

        cls.MSG_CLASS_TO_EVENT_TYPE = {v:k for k, v in cls.EVENT_TYPE_TO_MSG_CLASS.items()}

    @classmethod
    def from_parts(cls, host, port, token):
        url = f"ws://{host}:{port}/websocket?token={token}"
        return cls(url)

    def __init__(self, url):
        self.url = url
        self.sent_history = []
        self.received_history = []

        asyncio.get_event_loop().run_until_complete(self.connect(self.url))
        asyncio.get_event_loop().run_until_complete(self.register())
        
    async def connect(self, url):
        self.socket = await websockets.connect(url, ping_interval=None)
        
    async def register(self):
        message = RegisterViewer()
        # TODO remove this numpy dependency!
        message.session_id = np.uint32(uuid.uuid4().int % np.iinfo(np.uint32()).max) # why?
        
        await self.send_(message)
        self.sent_history.append(message)
        data = await self.socket.recv()
        
        reply = self.unpack(data)
        print("RECEIVED", reply.__class__.__name__)
        self.received_history.append(reply)
                
    async def send_(self, message):
        print("SENDING", message.__class__.__name__)
        await self.socket.send(self.pack(message))
        self.sent_history.append(message)
        
    def send(self, message):
        asyncio.get_event_loop().run_until_complete(self.send_(message))
                
    async def receive_(self):
        messages = []
        
        while True:
            try:
                data = await asyncio.wait_for(self.socket.recv(), timeout=1)
                message = self.unpack(data)
                print("RECEIVED", message.__class__.__name__)
                messages.append(message)
                await asyncio.sleep(1)
            except asyncio.TimeoutError:
                break
        
        self.received_history.extend(messages)
        return messages
            
    def receive(self):
        return asyncio.get_event_loop().run_until_complete(self.receive_())
        
    def pack(self, message):
        try:
            event_type = self.MSG_CLASS_TO_EVENT_TYPE[message.__class__]
        except KeyError:
            raise ValueError(f"{message.__class__.__name__} is not a valid event class.")
        
        # TODO remove this numpy dependency!
        header = struct.Struct('HHI').pack(event_type, MAJOR_VERSION, uuid.uuid4().int % np.iinfo(np.uint32()).max)
        
        return header + message.SerializeToString()
        
    def unpack(self, data):
        event_type, icd_version, message_id = struct.Struct('HHI').unpack(data[:8])
        try:
            event_class = self.EVENT_TYPE_TO_MSG_CLASS[event_type]
        except KeyError:
            raise ValueError(f"{event_type} is not a valid event type.")
        
        message = event_class()
        message.ParseFromString(data[8:])
        
        return message
    
    def clear(self):
        self.sent_history = []
        self.received_history = []

Client.init_event_maps()
