# HSS - Skill

Library for creating skills based on the [Hermes Skill Server](https://github.com/patrickjane/hss-server).

## Installation

Simply use `pip`:

```
(hss) pi@ceres:~/development/myskill $ pip3 install hss_skill
```


## Overview
The `hss_skill` package contains tools for fast and easy development of skills for the [Hermes Skill Server](https://github.com/patrickjane/hss-server). The goal is to let skill developers only care about their own skill implementation, while the internal stuff (communication with the skill-server, reading configuration, etc) is provided out-of-the-box by the `hss_skill` package.

The package provides a base class for skills `BaseSkill` which does all the incovenient stuff, like communication with the skill server, reading configuration file etc.    

### Abstract methods
When developing skills, a subclass of `BaseSkill` **must** implement two abstract methods, both of which are **coroutines**:    

##### `async def get_intentlist()`

The implementation shall return a list of intents handled by your skill. This will be used in the `hss-server` to detect/avoid duplicate intent registration.


##### `async def handle(request, session_id, site_id, intent_name, slots)`

The implementation should add program logic here to perform actual intent handling. Usually, the parameters `intent_name` and `slots` might be sufficient, however the full original intent is provided in the `request` parameter, and `session_id` and `site_id` can be used to do session- and site-based intent handling.

The implementation of this method should *usually* return with the execution of either `BaseSkill.answer` or `BaseSkill.followup`.



### Convenience methods

In addition, `BaseSkill` provides several methods which aid in skill development.

##### `def answer(session_id, site_id, response_message, lang)`

The `answer`-method should be called after the intent has been fully handled. This method also allows to send a response-text, which will then be forwarded to the TTS the your voice assistant. 

The parameters `session_id` and `site_id` should be the ones provided by `handle`, while the `text` parameter shall be the text which shall be asked by the voice assistant.

##### `def followup(session_id, site_id, question, lang, intent_filter = None)`

The `followup `-method should be called when the skill does not yet want to finish handling, but instead needs to ask for additional input. The `question`-text will be forwarded to the TTS of the voice assistant. In addition, a filter for intents (array of strings) can be given (see [hermes protocol docs](https://docs.snips.ai/reference/dialogue#continue-session)).

The parameters `session_id` and `site_id` should be the ones provided by `handle`, while the `question` parameter shall be the text which shall be asked by the voice assistant.

##### `async def say(text, siteId = None, lang = None)`

The `say` coroutine can be used to trigger the voice assistant to say a given text using its TTS. There is no further session- or intent handling involved. Since `say` is a **coroutine**, it must be `await`-ed.

##### `async def ask(text, siteId = None, lang = None, intent_filter = None)`

The `ask` coroutine can be used to start a new session. This will usually cause the voice assistant to speak the provided `text` using its TTS, and then listen for intents. Recognized intents may then be processed again.

Optionally, an `intent_filter` (array of strings) can be given which will be forwarded to the voice assistant (see [hermes protocol docs](https://docs.snips.ai/reference/dialogue#start-session)).

Since `ask` is a **coroutine**, it must be `await`-ed.


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
    skill = myskill.MoodSkill()
    skill.run()
```



#### myskill.py

```
from hss_skill import hss

class MoodSkill(hss.BaseSkill):
    def __init__(self):
        super().__init__()   # important, call super's constructor

    async def get_intentlist(self):
        return ["howAreYou"]

    async def handle(self, request, session_id, site_id, intent_name, slots):
        return self.answer(session_id, site_id, "Thanks, I am fine")
```

#### requirements.txt

```
hss_skill>=0.1.2
```

## Timers

The `BaseSkill` class provides a convenience method for setting up timers, which will execute a given callback function after a given timeout. This might be useful if the skill wants to trigger actions on its own at a given time.

Currently, as a limitation, only one timer can be active at a time. This will most likely change in the future, so that an arbitrary number of timers can be scheduled.

For this, two coroutines are provided:

##### `async def timer(timeout, callback, user = None, reschedule = False)`

Schedules a new timer. `timeout` shall be `int` and denote the numer of seconds until the provided **coroutine** `callback` is executed. If `user` is given, it will be passed to `callback` upon execution.

If a timer is already running, new scheduling will fail unless `True` is given for `reschedule`. In the latter case, the previous timer will be cancelled before a new timer is scheduled.

##### `async def cancel_timer(strict = True)`

Cancels an existing timer. If `True` is given for `strict`, an error message will be printed when `cancel_timer` is called but no timer is running.

### Example

```
    async def handle(self, request, session_id, site_id, intent_name, slots):
    
        ... # skill handling code
        
        # schedule timer in 10 seconds

        await self.timer(10, self.do_timer, "Can I ask you a question?", reschedule = True)
        
        # finish intent handling

        return self.answer(session_id, site_id, response_message)

    async def do_timer(self, text):
    
        # ask a question
        
        await self.ask(text, siteId = "default", intent_filter = ["s710:confirm", "s710:reject"])
```


## Skill installation
Please refer to [Hermes Skill Server](https://github.com/patrickjane/hss-server).