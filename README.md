# HSS - Skill

Library for creating skills based on the [Hermes Skill Server](https://github.com/patrickjane/hss-server).

## Installation

Simply use `pip`:

```
pip3 install hss_skill
```


## Overview
The `hss_skill` package contains tools for fast and easy development of skills for the [Hermes Skill Server](https://github.com/patrickjane/hss-server). The goal is to let skill developers only care about their own skill implementation, while the internal stuff (communication with the skill-server, reading configuration, etc) is provided out-of-the-box by the `hss_skill` package.

The package provides a base class for skills `BaseSkill` which does all the incovenient stuff, like communication with the skill server, reading configuration file etc.    

### Abstract methods
When developing skills, a subclass of `BaseSkill` **must** be implemented, which overwrites two abstract methods:    

- `get_intentlist` - shall return a list of intents handled by your skill
- `handle` - the actual entry point for handling intents of your skill

### Done-method

In addition, `BaseSkill` provides the `done`-method, which should be called after the intent has been fully handled. This method also allows to send response-messages, which will then be forwarded to the TTS of your voice assistant. This function has the following signature:

```
done(session_id, site_id, intent_name, response_message, lang)
```

Parameter explanation:

- `session_id` - same as provided by the `handle` method
- `site_id ` - same as provided by the `handle` method
- `intent_name ` - same as provided by the `handle` method
- `response_message` - *optional*: your message which shall be sent to the TTS
- `lang` - *optional*: language code which will be passed as well to the TTS (defaults to `en_GB`) 

### main.py

Skills must provide the file `main.py`, which is the file the skill-server is going to run. This file should create an instance of your skill class, and then call the `run` method of the skill.

### Configuration

`hss_skill` automatically read a configuration file `config.ini` if it is present in your skills root-folder. The configuration will be provided to the skill-class via `self.config`.

### Dependencies

Further dependencies can be defined in the file `requirements.txt` which should at least contain the dependency to `hss_skill`.


## Example

A minimum example of using `hss_skill`. The folder contents might look like:

- `main.py`
- `myskill.py`
- `config.ini`
- `requirements.txt`

#### main.py

```
import myskill

if __name__ == "__main__":
    skill = myskill.WeatherSkill()
    skill.run()
```



#### myskill.py

```
from hss_skill import hss

class WeatherSkill(hss.BaseSkill):
    def __init__(self):
        super().__init__()   # important, call super's constructor

    def get_intentlist(self):
        return ["howAreYou"]

    def handle(self, request, session_id, site_id, intent_name, slots):
        return self.done(session_id, site_id, intent_name, "Thanks, I am fine")
```

#### requirements.txt

```
hss_skill>=0.1.2
certifi
geopy>=1.20.0
requests>=2.22.0
```

## Skill installation
Please refer to [Hermes Skill Server](https://github.com/patrickjane/hss-server).