"""Pure topic contracts for the desktop data broker; no domain imports or I/O."""
import json
from typing import Callable, NamedTuple
from types import MappingProxyType

MAX_FRAME = 262144
MAX_RESULT = MAX_FRAME // 2


def fields(value, schema):
    if not isinstance(value, dict):
        raise ValueError("invalid-result")
    for key, types in schema.items():
        if key in value and type(value[key]) not in types:
            raise ValueError("invalid-result")


def objects(value):
    if not isinstance(value, list) or any(not isinstance(entry, dict) for entry in value):
        raise ValueError("invalid-result")
    return value


number = (int, float)
nullable_number = (int, float, type(None))


def _validate_network(result):
    fields(result, {"blocked": (bool,), "wired": (bool,), "backend": (str,)})
    for device in objects(result.get("devices")):
        fields(device, {"name": (str,), "state": (str,), "powered": (bool,), "scanning": (bool,), "details": (dict,)})
        for network in objects(device.get("networks", [])):
            fields(network, {"strength": nullable_number, "available": (bool,), "known": (bool,),
                             "connected": (bool,), "name": (str,)})


def _validate_latency(result):
    if "ping" not in result:
        raise ValueError("invalid-result")
    fields(result, {"ping": nullable_number, "loss": nullable_number})


def _validate_capture(result):
    if any(type(result.get(key)) is not bool for key in ("running", "ready", "recording", "paused", "streaming")):
        raise ValueError("invalid-result")
    fields(result, {"recordingSeconds": number, "recordingBytes": number, "streamingSeconds": number,
                    "scenes": (list,), "mic": (dict,), "webcam": (dict,)})


def _validate_capture_options(result):
    for key in ("audio", "mic", "webcam"):
        if key in result:
            fields(result[key], {"enabled": (bool,), "available": (bool,), "sources": (list,)})


def _validate_power(result):
    fields(result, {"available": (bool,), "enabled": (bool,), "percent": number,
                    "health": number, "hours": number, "status": (str,), "active": (str,), "profiles": (list,)})


def _validate_display_settings(result):
    if not isinstance(result.get("main"), str):
        raise ValueError("invalid-result")
    fields(result, {"saved": (dict,)})
    for monitor in objects(result.get("monitors")):
        if not isinstance(monitor.get("name"), str):
            raise ValueError("invalid-result")
        fields(monitor, {"mode": (str,), "position": (str,), "scale": (str,), "mirror": (str, type(None)),
                         "anchor": (dict, type(None)), "hdr": (bool,), "hdr_capable": (bool,),
                         "sdr_brightness": number, "modes": (list,)})
        if any(not isinstance(mode, str) for mode in monitor.get("modes", [])):
            raise ValueError("invalid-result")


def _validate_display_topology(result):
    fields(result, {"primary": (str,), "preferred": (list,), "windowGaps": (list,), "screenGaps": (list,)})
    if "monitors" in result:
        objects(result["monitors"])


def _validate_display_control(result):
    fields(result, {"available": (bool,), "enabled": (bool,), "scheduled": (bool,), "value": number,
                    "maximum": number, "kind": (str,), "name": (str,), "mode": (str,), "start": (str,), "end": (str,)})


def _validate_hardware(result):
    fields(result, {"identity": (dict,)})
    for section in objects(result.get("sections", [])):
        fields(section, {"usage": nullable_number, "rows": (list,), "title": (str,), "name": (str,)})


def _validate_remote(result):
    fields(result, {"allowed": (bool,), "tailscale": (dict,), "streaming": (dict,)})


def _validate_weather(result):
    fields(result, {key: (str,) for key in ("text", "source", "location", "condition", "temp", "feels", "wind", "humidity", "forecast")})
    for day in objects(result.get("forecastDays", [])):
        fields(day, {"day": (str,), "icon": (str,), "high": (str,), "low": (str,)})


def _validate_ai(result):
    fields(result, {"updated": number})
    for provider in objects(result.get("providers")):
        fields(provider, {"name": (str,)})
        for account in objects(provider.get("accounts", [])):
            fields(account, {"id": (str,), "label": (str,), "plan": (str, type(None))})
            for window in objects(account.get("windows", [])):
                fields(window, {"label": (str,), "used": number, "reset": nullable_number})


def _validate_updates(result):
    fields(result, {"state": (str,), "count": (int,), "repository": (int,), "aur": (int,), "downloadBytes": (int,)})
    if any(result.get(key, 0) < 0 for key in ("count", "repository", "aur", "downloadBytes")):
        raise ValueError("invalid-result")


class TopicDefinition(NamedTuple):
    name: str
    domain: str
    interval: float
    read_budget: float | None
    validator: Callable[[dict], None]

    def budget(self, timeout):
        budget = timeout if self.read_budget is None else self.read_budget
        return min(budget, timeout) if timeout < 5 else budget


_DEFINITIONS = (
    TopicDefinition("updates.status", "updates", 21600, 365, _validate_updates),
    TopicDefinition("weather.default", "weather", 900, 17, _validate_weather),
    TopicDefinition("ai.usage", "ai", 300, None, _validate_ai),
    TopicDefinition("remote.availability", "remote", float("inf"), None, _validate_remote),
    TopicDefinition("remote.status", "remote", 10, 10, _validate_remote),
    TopicDefinition("hardware.details", "hardware", 2, None, _validate_hardware),
    TopicDefinition("display.topology", "display", float("inf"), 16, _validate_display_topology),
    TopicDefinition("display.settings", "display", float("inf"), 6, _validate_display_settings),
    TopicDefinition("display.brightness", "display", 3, 9, _validate_display_control),
    TopicDefinition("display.nightlight", "display", 3, None, _validate_display_control),
    TopicDefinition("network.summary", "network", 10, None, _validate_network),
    TopicDefinition("network.details", "network", 2, None, _validate_network),
    TopicDefinition("network.latency", "network", 15, None, _validate_latency),
    TopicDefinition("power.battery", "power", 30, None, _validate_power),
    TopicDefinition("power.profile", "power", 5, None, _validate_power),
    TopicDefinition("power.radios", "power", 5, None, _validate_power),
    TopicDefinition("capture.summary", "capture", 2, 10, _validate_capture),
    TopicDefinition("capture.details", "capture", 2, 25, _validate_capture),
    TopicDefinition("capture.options", "capture", float("inf"), None, _validate_capture_options),
)
TOPICS = MappingProxyType({definition.name: definition for definition in _DEFINITIONS})
INTERVALS = MappingProxyType({name: definition.interval for name, definition in TOPICS.items()})


def validate_result(topic, result):
    """Validate CLI data without confusing absent capabilities with read failures."""
    if not isinstance(result, dict):
        raise ValueError("invalid-result")
    if len(json.dumps(result, allow_nan=False).encode()) > MAX_RESULT:
        raise ValueError("oversize-result")
    definition = TOPICS.get(topic)
    if definition is not None:
        definition.validator(result)
