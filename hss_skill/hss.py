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
import asyncio

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

        # variables

        self.args = self.parse_args()
        self.config = None
        self.debug = True if "debug" in self.args else False
        self.develop = True if "develop" in self.args else False
        self.timer_task = None
        self.default_language = None
        self.slot_dictionary = None
        self.name = self.args["skill-name"]
        self.port = int(self.args["port"])
        self.parent_port = int(self.args["parent-port"]) if "parent-port" in self.args else None

        # setup logger

        self.log = logging.getLogger("skill:{}".format(self.name))

        # determine absolute file paths for config.ini and skill.json

        try:
            root_path = os.path.abspath(sys.modules['__main__'].__file__).replace("main.py", "")
            self.config_path = os.path.join(root_path, "config.ini")
            self.skill_json_path = os.path.join(root_path, "skill.json")
        except Exception as e:
            self.log.error("Setting config path failed ({})".format(e))

        # open config.ini, if present

        if os.path.exists(self.config_path) and os.path.isfile(self.config_path):
            self.config = configparser.ConfigParser()
            self.config.read(self.config_path)

            # get language from config.ini

            if "skill" in self.config and "language" in self.config["skill"]:
                self.default_language = self.config["skill"]["language"]

        # open skill.json (must be present)

        with open(self.skill_json_path) as json_file:
            self.skill_json = json.load(json_file)

        # get default language from skill.json (if not configured in config.ini)

        if "language" in self.skill_json and not self.default_language:
            self.default_language = self.skill_json["language"]

            if isinstance(self.default_language, list):
                self.default_language = self.default_language[0]

        # fall back to english if no language at all available

        if not self.default_language:
            self.default_language = "en_GB"

        # build slot dictionary for current language, if present
        # (map slotText -> slotIdent)

        slot_dict_filename = "slotsdict.{}.json".format(self.default_language).lower()
        slot_dict_filepath = os.path.join(root_path, slot_dict_filename)

        if os.path.exists(slot_dict_filepath) and os.path.isfile(slot_dict_filepath):
            slotdict_json = None

            with open(slot_dict_filepath) as json_file:
                try:
                    slotdict_json = json.load(json_file)

                    self.slot_dictionary = { k: {v: key for key, values in sub_dict.items() for v in values}
                                                for k, sub_dict in slotdict_json.items() }
                except Exception as e:
                    self.log.warning("Failed to open '{}' ({})".format(slot_dict_filepath, e))

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
        if self.develop:
            print("WARNING: Not starting develop mode (--develop was given)")
            return

        self.rpc = rpc.RpcServer(self.port, self)
        self.rpc_client = rpc.RpcClient(self.parent_port)

        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.rpc_client.connect())
            loop.run_until_complete(self.rpc.start())
        except KeyboardInterrupt:
            pass
        except Exception as e:
            if e and len(str(e)):
                self.log.error("Got exception: {}".format(e))
        finally:
            self.log.info("Bye.")

    # --------------------------------------------------------------------------
    # timer
    # --------------------------------------------------------------------------

    async def timer(self, timeout, callback, user = None, reschedule = False):
        if self.timer_task and not reschedule:
            self.log.error("Cannot schedule timer, timer already active!")
            return

        if self.timer_task:
            await self.cancel_timer(strict = False)

        self.log.debug("Timer scheduled with delay of {} seconds".format(timeout))

        loop = asyncio.get_event_loop()

        self.timer_task = loop.create_task(self.timer_executor(timeout, callback, user))

    # --------------------------------------------------------------------------
    # cancel timer (async)
    # --------------------------------------------------------------------------

    async def cancel_timer(self, strict = True):
        if not self.timer_task:
            if strict:
                self.log.error("Can't cancel timer, no timer is active!")
            return

        self.timer_task.cancel()

        try:
            await self.timer_task
        except asyncio.CancelledError as e:
            pass

        self.timer_task = None

        self.log.debug("Timer cancelled")

    # --------------------------------------------------------------------------
    # timer_fn (async)
    # --------------------------------------------------------------------------

    async def timer_executor(self, timeout, callback, user):
        await asyncio.sleep(timeout)

        self.timer_task = None

        if user:
            await callback(user)
        else:
            await callback()

    # --------------------------------------------------------------------------
    # dispatch_rpc_request
    # --------------------------------------------------------------------------

    async def dispatch_rpc_request(self, command, payload):
        if command == 'get_intentlist':
            return await self.get_intentlist()

        elif command == 'handle':
            return await self.on_request(payload)

    # --------------------------------------------------------------------------
    # on_request
    # --------------------------------------------------------------------------

    async def on_request(self, request):
        def slot_value(name, rawvalue):
            if not self.slot_dictionary:
                return rawvalue

            if not name in self.slot_dictionary:
                return rawvalue

            if not rawvalue in self.slot_dictionary[name]:
                return rawvalue

            return self.slot_dictionary[name][rawvalue]

        if not "intent" in request or not "intentName" in request["intent"]:
            self.log.error("Received message without 'intentName', must skip")
            return False

        # extract common attributes

        intent_name = request["intent"]["intentName"]
        session_id = request["sessionId"] if "sessionId" in request else None
        site_id = request["siteId"] if "siteId" in request else None
        slots = request["slots"] if "slots" in request else None
        slots_dict = {}
        mapped_slots = {}

        # some convenience preparation for slots

        if slots and len(slots):
            try:
                for slot in slots:
                    if slot["slotName"] in slots_dict:
                        slots_dict[slot["slotName"]].append(
                            slot["value"]["value"])
                    else:
                        slots_dict[slot["slotName"]] = [slot["value"]["value"]]

                    # mapped slots is an additional map which holds the slotIdentifier instead of the raw language specific slot text
                    # the slotIdentifier is meant to be equal in all languages supported by the skill

                    if slot["slotName"] in mapped_slots:
                        mapped_slots[slot["slotName"]].append(
                            slot_value(slot["entity"], slot["value"]["value"]))
                    else:
                        mapped_slots[slot["slotName"]] = [slot_value(slot["entity"], slot["value"]["value"])]

                # recode single-value slots to literal. keep other slots as list-value

                for slot in slots_dict:
                    if len(slots_dict[slot]) == 1:
                        slots_dict[slot] = slots_dict[slot][0]

                for slot in mapped_slots:
                    if len(mapped_slots[slot]) == 1:
                        mapped_slots[slot] = mapped_slots[slot][0]

            except Exception as e:
                self.log.error(
                    "Failed to parse slots in JSON request, must skip request ({})".format(e))
                return False

        return await self.handle(request, session_id, site_id, intent_name, slots_dict, mapped_slots)

    # -------------------------------------------------------------------------
    # server -> skill RPC
    # -------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # handle (abstract)
    # --------------------------------------------------------------------------

    @abstractmethod
    async def handle(self, request, session_id, site_id, intent_name, slots, mapped_slots):
        pass

    # -------------------------------------------------------------------------
    # handle response helpers
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # done
    # -------------------------------------------------------------------------

    def answer(self, session_id, site_id, response_message, lang = None):
        return {
                "sessionId": session_id,
                "siteId": site_id,
                "text": response_message,
                "lang": lang if lang else self.default_language
            }

    # -------------------------------------------------------------------------
    # followup
    # -------------------------------------------------------------------------

    def followup(self, session_id, site_id,  question, lang = None, intent_filter = None):
        return {
                "sessionId": session_id,
                "siteId": site_id,
                "question": question,
                "lang": lang if lang else self.default_language,
                "intentFilter": intent_filter if intent_filter else None
            }

    # -------------------------------------------------------------------------
    # skill -> server RPC
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # say
    # -------------------------------------------------------------------------

    async def say(self, text, siteId = None, lang = None):
        await self.rpc_client.execute("say",
                                    {
                                        "text": text,
                                        "lang": lang if lang else self.default_language,
                                        "siteId": siteId if siteId else None
                                    })

    # -------------------------------------------------------------------------
    # ask
    # -------------------------------------------------------------------------

    async def ask(self, text, siteId = None, lang = None, intent_filter = None):
        await self.rpc_client.execute("ask",
                                    {
                                        "text": text,
                                        "lang": lang if lang else self.default_language,
                                        "siteId": siteId if siteId else None,
                                        "intentFilter": intent_filter if intent_filter else None
                                    })

