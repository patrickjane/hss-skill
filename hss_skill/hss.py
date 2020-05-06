# -----------------------------------------------------------------------------
# HSS - Hermes Skill Server - Skill module
# Copyright (c) 2020 - Patrick Fial
# -----------------------------------------------------------------------------
# hss.py
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
import configparser
import os
import sys
import json
from abc import ABCMeta, abstractmethod

from hss_skill import logger
from hss_skill import rpc

# -----------------------------------------------------------------------------
# class Skill (wrapper for loaded skills)
# -----------------------------------------------------------------------------


class BaseSkill(metaclass=ABCMeta):

    # --------------------------------------------------------------------------
    # ctor
    # --------------------------------------------------------------------------

    def __init__(self):
        logger.Logger.static_init(None)

        self.args = self.parse_args()
        self.config = None
        self.debug = False

        try:
            root_path = os.path.abspath(sys.modules['__main__'].__file__).replace("main.py", "")
            self.config_path = os.path.join(root_path, "config.ini")
        except Exception as e:
            self.log.error("Setting config path failed ({})".format(e))

        if os.path.exists(self.config_path) and os.path.isfile(self.config_path):
            self.config = configparser.ConfigParser()
            self.config.read(self.config_path)

        self.name = self.args["skill-name"]
        self.port = int(self.args["port"]) if "port" in self.args else 18861
        self.log = logging.getLogger("skill:{}".format(self.name))

        if "debug" in self.args:
            self.debug = True

    # --------------------------------------------------------------------------
    # parse_args
    # --------------------------------------------------------------------------

    def parse_args(self):
        def _getArg(a):
            try:
                res = a.split('=', 2)

                if len(res) == 1:
                    return res[0].replace('--', ''), None

                return res[0].replace('--', ''), res[1]
            except Exception as e:
                print("Failed to parse command line arguments ({})".format(e))
                return None

        return {kv[0]: kv[1] for kv in list(map(_getArg, sys.argv)) if kv != None}

    # --------------------------------------------------------------------------
    # run
    # --------------------------------------------------------------------------

    def run(self):
        rpc_logger = logging.getLogger('rpc')
        rpc_logger.setLevel(level=logging.ERROR)

        self.rpc_server = rpc.RpcServer.create_server(
            rpc.RpcService(self), port=self.port, logger=rpc_logger)
        self.rpc_server.start()

    # --------------------------------------------------------------------------
    # on_request
    # --------------------------------------------------------------------------

    def on_request(self, payload):
        try:
            request = json.loads(payload)
        except Exception as e:
            self.log.error(
                "Failed to parse JSON request, must skip request ({})".format(e))
            return False

        if not "intent" in request or not "intentName" in request["intent"]:
            self.log.error("Received message without 'intentName', must skip")
            return False

        # extract common attributes

        intent_name = request["intent"]["intentName"]
        session_id = request["sessionId"] if "sessionId" in request else None
        site_id = request["siteId"] if "siteId" in request else None
        slots = request["slots"] if "slots" in request else None
        slots_dict = {}

        # some convenience preparation for slots

        if slots and len(slots):
            try:
                for slot in slots:
                    if slot["slotName"] in slots_dict:
                        slots_dict[slot["slotName"]].append(
                            slot["value"]["value"])
                    else:
                        slots_dict[slot["slotName"]] = [slot["value"]["value"]]

                # recude single-value slots to literal. keep other slots as list-value

                for slot in slots_dict:
                    if len(slots_dict[slot]) == 1:
                        slots_dict[slot] = slots_dict[slot][0]

            except Exception as e:
                self.log.error(
                    "Failed to parse slots in JSON request, must skip request ({})".format(e))
                return False

        return self.handle(request, session_id, site_id, intent_name, slots_dict)

    # --------------------------------------------------------------------------
    # handle (abstract)
    # --------------------------------------------------------------------------

    @abstractmethod
    def handle(self, request, session_id, site_id, intent_name, slots):
        pass

    # --------------------------------------------------------------------------
    # get_intentlist (abstract)
    # --------------------------------------------------------------------------

    @abstractmethod
    def get_intentlist(self):
        pass

    # -------------------------------------------------------------------------
    # done
    # -------------------------------------------------------------------------

    def done(self, session_id, site_id, intent_name, response_message, lang):
        res = {"sessionId": session_id, "siteId": site_id,
               "intentName": intent_name, "text": response_message, "lang": lang if lang else "en_GB"}

        return json.dumps(res, ensure_ascii=False).encode('utf8')

