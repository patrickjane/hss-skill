# -----------------------------------------------------------------------------
# python skill server for home automation
# Copyright (c) 2020 - Patrick Fial
# -----------------------------------------------------------------------------
# logger.py
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging

# -----------------------------------------------------------------------------
# class Logger
# -----------------------------------------------------------------------------

class Logger:
    initialized = False

    def static_init(file_name, level=logging.INFO):
        if Logger.initialized:
            return None

        if file_name == None:
            logging.basicConfig(level=level,
                                format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')
        else:
            logging.basicConfig(filename=file_name,
                                level=level,
                                format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')

        Logger.initialized = True
