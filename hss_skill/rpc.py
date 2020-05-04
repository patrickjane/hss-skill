# -----------------------------------------------------------------------------
# HSS - Hermes Skill Server - Skill module
# # Copyright (c) 2020 - Patrick Fial
# -----------------------------------------------------------------------------
# rpc.py
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from rpyc.utils.server import OneShotServer
import rpyc

# -----------------------------------------------------------------------------
# class RpcServer
# -----------------------------------------------------------------------------


class RpcServer:
    def create_server(service, port, logger):
        return OneShotServer(service, port=port, logger=logger)

# -----------------------------------------------------------------------------
# class RpcService
# -----------------------------------------------------------------------------


class RpcService(rpyc.Service):
    def __init__(self, base_skill):
        self.base_skill = base_skill

    def exposed_handle(self, request):
        return self.base_skill.on_request(request)

    def exposed_get_intentlist(self):
        intents = self.base_skill.get_intentlist()
        return intents
