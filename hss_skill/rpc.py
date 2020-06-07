# -----------------------------------------------------------------------------
# HSS - Hermes Skill Server
# Copyright (c) 2020 - Patrick Fial
# -----------------------------------------------------------------------------
# rpc.py
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging

import asyncio
import json

# -----------------------------------------------------------------------------
# class RpcClient
# -----------------------------------------------------------------------------


class RpcClient:

    # --------------------------------------------------------------------------
    # ctor
    # --------------------------------------------------------------------------

    def __init__(self, port):
        self.log = logging.getLogger(__name__)
        self.port = port
        self.channel = None
        self.rpc_client = None
        self.reader = None
        self.writer = None

    # --------------------------------------------------------------------------
    # connect (async)
    # --------------------------------------------------------------------------

    async def connect(self):
        self.log.debug("Connecting to servers RPC port ...")

        self.reader, self.writer = await asyncio.open_connection('127.0.0.1', self.port)

    # --------------------------------------------------------------------------
    # disconnect (async)
    # --------------------------------------------------------------------------

    async def disconnect(self):
        if self.writer:
            self.log.info("Disconnecting")
            self.writer.close()
            await self.writer.wait_closed()

    # --------------------------------------------------------------------------
    # execute (async)
    # --------------------------------------------------------------------------

    async def execute(self, command, payload = None):
        package = { "command": command, "payload": payload }

        json_string = json.dumps(package, ensure_ascii=False).replace('\n', '\\n') + '\n'

        self.writer.write(json_string.encode('utf8'))
        await self.writer.drain()

        response = await self.reader.readline()

        try:
            response_obj = json.loads(response.decode("utf-8").replace('\\n', '\n')) if response else None
        except Exception as e:
            self.log.error("Received malformed RPC response ({})".format(e))
            return

        if "payload" not in response_obj:
            self.log.error("Missing mandatory property 'payload' in RPC response")
            return None

        return response_obj["payload"]

# -----------------------------------------------------------------------------
# class RpcServer
# -----------------------------------------------------------------------------


class RpcServer:

    # --------------------------------------------------------------------------
    # ctor
    # --------------------------------------------------------------------------

    def __init__(self, port, base_skill):
        self.log = logging.getLogger(__name__)

        self.port = port
        self.base_skill = base_skill
        self.server = None

    # --------------------------------------------------------------------------
    # start (async)
    # --------------------------------------------------------------------------

    async def start(self):
        self.server = await asyncio.start_server(self.on_connected, '127.0.0.1', self.port)
        await self.server.serve_forever()

    # --------------------------------------------------------------------------
    # stop (async)
    # --------------------------------------------------------------------------

    async def stop(self):
        if not self.server:
            return

        self.log.info("Shutting down RPC server ...")

        try:
            self.server.close()
            await self.server.wait_closed()
        except Exception as e:
            self.log.error("Error while shutting down server: {}".format(e))

    # --------------------------------------------------------------------------
    # on_connected (async)
    # --------------------------------------------------------------------------

    async def on_connected(self, reader, writer):
        async def abort():
            try:
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                pass

            await self.stop()

        # stream reader loop

        while True:
            res = None

            try:
                data = await reader.readline()
            except Exception as e:
                self.log.error("Failed to read RPC connection ({})".format(e))
                break;

            # bail out and abort if anything on RPC level is weird

            try:
                json_string = data.decode("utf-8").replace('\\n', '\n')
                request_obj = json.loads(json_string) if data else None
            except Exception as e:
                self.log.error("Failed to parse RPC request ({})".format(e))
                return await abort()

            if not request_obj:
                self.log.error("Malformed RPC request from server received, shutting down")
                return await abort()

            # otherwise process RPC request

            try:
                self.log.debug("Got new RPC request with command '{}'".format(
                    request_obj["command"] if "command" in request_obj else ""))

                if not request_obj or "command" not in request_obj or "payload" not in request_obj:
                    self.log.error("Received malformed RPC request (missing mandatory json propertis 'command'/'payload'")
                    return

                res = await self.base_skill.dispatch_rpc_request(request_obj["command"], request_obj["payload"])

                if not res:
                    return

                json_string = json.dumps({"payload": res}, ensure_ascii=False).replace('\n', '\\n') + '\n'

                writer.write(json_string.encode('utf8'))
                await writer.drain()
            except Exception as e:
                self.log.error("Handling RPC request failed ({})".format(e))

        if do_close:
            await self.stop()