import json
import os

STATE_FILE = "state.json"

state = {}

def load_state():
    global state
    if not os.path.exists(STATE_FILE):
        state = {"users": {}, "items": {}, "world": {}, "arena_world": {}, "lab_world": {}, "voidmaze_world": {}}
        save_state()
        return state

    with open(STATE_FILE, "r") as f:
        state = json.load(f)

    return state


def save_state():
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
