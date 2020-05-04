# Hermes Skill Server - Skill

Library for creating skills based on the Hermes Skill Server.

## Usage

```
pip3 install hss-skill
```

The bare minimum to create a skill using `hss-skill`:

**main.py**

```
import skill

if __name__ == "__main__":
    skill = skill.Skill()
    skill.run()
```



**skill.py**

```
import hss

class Skill(hss.BaseSkill):
    def __init__(self):
        super().__init__()   # important

    def get_intentlist(self):
        return ["howAreYou"]

    def handle(self, request, session_id, site_id, intent_name, slots):
        return self.done(session_id, site_id, intent_name, "Thanks, I am fine")
```

## Details

- `main.py` must be implemented, and it must call `.run()` on the instance of a `hss.BaseSkill` subclass
- The `hss.BaseSkill` subclass must overwrite `get_intentlist` and `handle`
- `get_intentlist` must return a list of strings, each string representing an intent this skill can handle
   - When defining intent names, make sure not to collide with other developers intent names, as the skill server will not run your skill if it provides already registered intents (e.g. use `'johndoe:howAreYou'` instead of `'howAreYou'`)
- `handle` will be called every time one of the skill's intent was detected. You *should* call the base class' method `done` when done handling the intent. If given a message, `done` will cause the skill server to speak your message via TTS
- The skill directory can optionally contain a configuration file `config.ini`. If present, your subclass will have access to that config via `self.config`
- A file "requirements.txt" *should* be present if your skill depends on external modules
