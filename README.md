# HSS - Skill

Library for creating skills based on the [Hermes Skill Server](https://github.com/patrickjane/hss-server).

A Node.JS library is also available, check out [HSS-Skill](https://github.com/patrickjane/node-hss-skill).

# Installation

Simply use `pip`:

```
(hss) pi@ceres:~/development/myskill $ pip3 install hss_skill
```


# Overview
The `hss_skill` package contains tools for fast and easy development of skills for the [Hermes Skill Server](https://github.com/patrickjane/hss-server). The goal is to let skill developers only care about their own skill implementation, while the internal stuff (communication with the skill-server, reading configuration, etc) is provided out-of-the-box by the `hss_skill` package.

The package provides a base class for skills `BaseSkill` which does all the incovenient stuff, like communication with the skill server, reading configuration file etc.

# Getting started

Your skill implementation must provide the following components:

- installed `hss_skill` module
- `main.py` file as entrypoint
- `skill.json` file containing meta infos about your skill
- your skill implementation (e.g. `myskill.py`)
- `requirements.txt` file containing python dependencies, at least `hss_skill`
- [optional] `config.ini.default` file containing your skill's configuration (default) parameters

In addition, for interaction with `rhasspy` voice assistant:

- [optional] `sentences.ini` containing the sentences `rhasspy` should use (only YOUR SKILLs sentences)
- [optional] `slots.json` containing slot definitions your skill uses

If `sentences.ini` is provided, `hss-cli` will register the sentences at `rhasspy` upon skill installation, and trigger `rhasspy` for training.

Same applies to `slots.json`.

In order to support multiple languages, a skill may have the following files instead of `slots.json` and `sentences.ini`: 

- `slotsdict.[LANG].json` (multiple, one per language with `LANG` beeing the language code in lower case, e.g. "de_de")
- `sentences.[LANG].ini` (multiple, one per language with `LANG` beeing the language code in lower case, e.g. "de_de") 

## Boilerplate

Your `main.py` might be sufficient if it looks roughly like this:

```
import myskill

if __name__ == "__main__":
    skill = myskill.MoodSkill()
    skill.run()
```

Your `requirements.txt` could look like:

```
hss_skill>=0.4.2
certifi
geopy>=1.20.0
requests>=2.22.0
```

## Your skill implementation

When developing skills, a subclass of `BaseSkill` **must** implement the **coroutine**:

#### `async def handle(request, session_id, site_id, intent_name, slots, mapped_slots)`

A coroutine which is called every time an intent which was registered by your skill is recognized and should be answered.

Usually, the parameters `intent_name` and `slots` might be sufficient, however the full original intent is provided in the `request` parameter, and `session_id` and `site_id` can be used to do session- and site-based intent handling.

The implementation of this method should *usually* return with the execution of either `BaseSkill.answer` or `BaseSkill.followup` to finish intent handling (see below).

To support multiple languages with one skill implementation, `mapped_slots` is provided, which contains each slot translated to a slot-identifier (instead of the raw slot string). See chapter "Multiple languages support".


### Example

A minimal example of a skill (myskill.py) might look as:


```
from hss_skill import hss

class MoodSkill(hss.BaseSkill):
    def __init__(self):
        super().__init__()   # important, call super's constructor

    async def handle(self, request, session_id, site_id, intent_name, slots, mapped_slots):
        return self.answer(session_id, site_id, "Thanks, I am fine")
```


## Contents of `skill.json`

The `skill.json` is a mandatory file containing meta info about your skill. It is used both during installation as well as when your skill is run.

It could look like the following:

```
{
    "platform": "hss-python",
    "type": "weather",
    "name": "hss-s710-mood",
    "version": "1.0.0",
    "author": "Some Dude",
    "intents": ["s710:howAreYou"],
    "shortDescription": "Some funny chatting",
    "language": "en_GB"
}
```

Properties explained:

##### `platform` (mandatory)

Must be `hss-python`, stating the skill is a python based HSS skill.

#### `type` (mandatory)

Type of skill, e.g. `weather`. Must be one of:

- `weather`
- `calendar`
- `music`
- `datetime`
- `news`
- `games`
- `fun`
- `utility`
- `automation`

#### `version` (mandatory)

The version number of the skill.

#### `author` (mandatory)

The name of the author of the skill.

#### `intents` (mandatory)

An array of strings containing all intents the skill can handle.

#### `shortDescription` (mandatory)

A short description of your skill. Will be shown in the HSS registry skill list.

#### `version` (optional)

A string describing your skill's version.

#### `language` (mandatory)

A four-letter code string determining your skill's default language. When the skill supports more than one language, this property shall be an array (e.g. `["de_DE", "en_GB"]`).


## Base class

In addition, `BaseSkill` provides several methods and properties which aid in skill development.

#### `BaseSkill.log`

Logger object which can be used for logging.

#### `BaseSkill.default_language`

The default language as determined by the `BaseSkill` class.

Can be changed by the skill implementation any time to affect the behaviour of the below mentioned methods.

The default language is determined in the follow way (and order):    

- config.ini section `skill` parameter `language`
- skill.json `language` property (first language, if `language` is an array)
- fall back to `en_GB`


#### `def answer(session_id, site_id, response_message, lang)`

The `answer`-method should be called after the intent has been fully handled. This method also allows to send a response-text, which will then be forwarded to the TTS the your voice assistant.

The parameters `session_id` and `site_id` should be the ones provided by `handle`, while the `text` parameter shall be the text which shall be asked by the voice assistant.

If the `lang` parameter is not given, `BaseSkill.default_language` will be used.

#### `def followup(session_id, site_id, question, lang, intent_filter = None)`

The `followup `-method should be called when the skill does not yet want to finish handling, but instead needs to ask for additional input. The `question`-text will be forwarded to the TTS of the voice assistant. In addition, a filter for intents (array of strings) can be given (see [hermes protocol docs](https://docs.snips.ai/reference/dialogue#continue-session)).

The parameters `session_id` and `site_id` should be the ones provided by `handle`, while the `question` parameter shall be the text which shall be asked by the voice assistant.

If the `lang` parameter is not given, `BaseSkill.default_language` will be used.

#### `async def say(text, siteId = None, lang = None)`

The `say` coroutine can be used to trigger the voice assistant to say a given text using its TTS. There is no further session- or intent handling involved.

If the `lang` parameter is not given, `BaseSkill.default_language` will be used.

Since `say` is a **coroutine**, it must be `await`-ed.

#### `async def ask(text, siteId = None, lang = None, intent_filter = None)`

The `ask` coroutine can be used to start a new session. This will usually cause the voice assistant to speak the provided `text` using its TTS, and then listen for intents. Recognized intents may then be processed again.

If the `lang` parameter is not given, `BaseSkill.default_language` will be used.

Optionally, an `intent_filter` (array of strings) can be given which will be forwarded to the voice assistant (see [hermes protocol docs](https://docs.snips.ai/reference/dialogue#start-session)).

Since `ask` is a **coroutine**, it must be `await`-ed.



### Timers

The `BaseSkill` class provides a convenience method for setting up timers, which will execute a given callback function after a given timeout. This might be useful if the skill wants to trigger actions on its own at a given time.

Currently, as a limitation, only one timer can be active at a time. This will most likely change in the future, so that an arbitrary number of timers can be scheduled.

For this, two coroutines are provided:

#### `async def timer(timeout, callback, user = None, reschedule = False)`

Schedules a new timer. `timeout` shall be `int` and denote the numer of seconds until the provided **coroutine** `callback` is executed. If `user` is given, it will be passed to `callback` upon execution.

If a timer is already running, new scheduling will fail unless `True` is given for `reschedule`. In the latter case, the previous timer will be cancelled before a new timer is scheduled.

#### `async def cancel_timer(strict = True)`

Cancels an existing timer. If `True` is given for `strict`, an error message will be printed when `cancel_timer` is called but no timer is running.

### Example

```
    async def handle(self, request, session_id, site_id, intent_name, slots, mapped_slots):

        ... # skill handling code

        # schedule timer in 10 seconds

        await self.timer(10, self.do_timer, "Can I ask you a question?", reschedule = True)

        # finish intent handling

        return self.answer(session_id, site_id, response_message)

    async def do_timer(self, text):

        # ask a question

        await self.ask(text, siteId = "default", intent_filter = ["s710:confirm", "s710:reject"])
```

### Multiple languages support

In order to support more than one language, a skill might need the following:

- sentences in all supported languages
- slots in all supported languages
- determination of current/active language
- easy handling of language specific slots in the code

`hss-skill` supports all of this, thus enabling developers to easily implement more than one language in their skills.

#### sentences.ini

In order to support more than one language, instead of providing a file named `sentences.ini`, provide one file per language, and include the language code (lowercase) in the filename:

- `sentences.de_de.ini`
- `sentences.en_gb.ini`

#### slots

In order to support more than one language, instead of providing a file named `slots.json`, provide one file per language, and include the language code (lowercase) in the filename. Also, the file does not contain arrays, but dictionary instead:

- `slotsdict.de_de.json`
- `slotsdict.en_gb.json`

The idea is, that it will be cumbersome to work with the localized, language-specific slot strings in the code, when multiple languages are involved. Therefore, the `slotsdict.json` files provide a mapping from localized ("real") slots strings to slot-identifiers, which will be the same for every language. Those slot-identifiers will be provided to the `handle()` method in the `mapped_slots` parameters.

The files might contain:

```
slotsdict.de_de.json:

{
   "relative_time": {
      "now": ["jetzt", "gerade", "später", "nachher", "gegen später"],
      "today": ["heute"],
      "todayMorning": ["heute früh", "heute morgen"]
   }
}

slotsdict.en_gb.json:

{
   "relative_time": {
      "now": ["now", "right now", "later", "then", "towards later", "around later"],
      "today": ["today"],
      "todayMorning": ["this morning", "ealier today"]
   }
}
```

So, if, for example, a slot with the text "nachher" is recognized (with german language enable), `handle()` will receive `nachher` in the `slots` parameter, and `now` in the `mapped_slots` parameter.

If a slot with the text "right now" is recognized (with english language enable), `handle()` will receive `right now` in the `slots` parameter, and `now` in the `mapped_slots` parameter.

This means, that the skill implementation can rely on a language-independent slot-identifer (`now` in the above example) while still having access to the original, language-specific slot value (`nachher`/`right now`).

When installing a skill with the above slot-dictionaries, `hss-cli` will still register slots as usual at the voice assistant. It will, however, only register the slots for the language which is selected upon installation.

# Configuration

If your skill needs its own configuration parameters which must be supplied by the user (e.g. access tokens, ...), you can provide a `config.ini.default` file.

This file is meant to a) give default values for configuration options and b) contain empty configuration values, which must be filled by the user upon skill installation. See [Hermes Skill Server](https://github.com/patrickjane/hss-server) for details about skill installation.

Upon installation `config.ini.default` will be copied into `config.ini`, and values will be filled by the user. `config.ini.default` will remain untouched.

#### Example

```
[skill]
confirmation = I am okay, what about you?
```

In code, you can access the configuration using the `BaseSkill`'s `cfg` member. It will be a dictionary object resembling your configuration.

```
    async def handle(self, request, session_id, site_id, intent_name, slots, mapped_slots):
        return self.answer(session_id, site_id, self.cfg["skill"]["confirmation"])

```

# Skill installation
Please refer to [Hermes Skill Server](https://github.com/patrickjane/hss-server).
