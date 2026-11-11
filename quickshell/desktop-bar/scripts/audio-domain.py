"""Audio ports a sound card offers besides the ones its current profile uses: a second monitor
on the same graphics card, the analog jack beside the optical output, a front microphone. A
card plays through one profile at a time, so PipeWire only has devices for that profile's
ports; these are the others, read from pactl, and choosing one switches the card's profile.
Only ALSA cards: a Bluetooth headset's other profile is its low-quality call mode."""
import json
import subprocess
import time


def split(profile):
    """{'output': 'hdmi-stereo', 'input': 'analog-stereo'} for 'output:hdmi-stereo+input:analog-stereo'."""
    parts = {}
    for part in str(profile or "").split("+"):
        kind, _, name = part.partition(":")
        if kind in ("output", "input") and name:
            parts[kind] = name
    return parts


def ports(cards):
    """The available ports no current profile uses, each with the profile that reaches it
    (keeping the card's other direction where a profile allows) and the device it brings."""
    found = []
    for card in cards if isinstance(cards, list) else []:
        name = str(card.get("name") or "")
        if not name.startswith("alsa_card.") or not isinstance(card.get("ports"), dict):
            continue
        profiles = card.get("profiles") if isinstance(card.get("profiles"), dict) else {}
        active = str(card.get("active_profile") or "")
        current = split(active)
        description = str((card.get("properties") or {}).get("device.description") or "")
        # USB headsets list an optical output they do not have; there, only ports known
        # to be connected count.
        usb = (card.get("properties") or {}).get("device.bus") == "usb"
        for port_name, port in card["ports"].items():
            if not isinstance(port, dict) or port.get("availability") == "not available" \
                    or (usb and port.get("availability") != "available"):
                continue
            reachable = [profile for profile in port.get("profiles") or [] if isinstance(profile, str)
                         and (profiles.get(profile) or {}).get("available", True)]
            # Which way the port goes: only an output port sits in an output-only profile.
            direction = next((kind for kind in ("output", "input")
                              if any(set(split(profile)) == {kind} for profile in reachable)), "")
            if not direction or active in reachable:
                continue
            other = "input" if direction == "output" else "output"
            candidates = [profile for profile in reachable if direction in split(profile)]
            keeping = [profile for profile in candidates if split(profile).get(other) == current.get(other)]
            chosen = max(keeping or candidates, key=lambda profile: (profiles.get(profile) or {}).get("priority", 0))
            props = port.get("properties") if isinstance(port.get("properties"), dict) else {}
            found.append(dict(
                card=name, profile=chosen, port=str(port_name), direction=direction,
                node=("alsa_output." if direction == "output" else "alsa_input.") + name[len("alsa_card."):]
                     + "." + split(chosen)[direction],
                monitor=str(props.get("device.product.name") or ""), kind=str(props.get("port.type") or ""),
                label=str(port.get("description") or port_name), device=description))
    return found


class AudioDomain:
    def pactl(self, arguments, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("audio-timeout")
        return subprocess.run(["pactl", *arguments], capture_output=True, text=True, check=True,
                              timeout=min(5, remaining)).stdout

    def query(self, name, args, deadline):
        if name == "ports":
            return dict(ports=ports(json.loads(self.pactl(["-f", "json", "list", "cards"], deadline) or "[]")))
        # Only a port this read offers can be chosen, so the profile is always a real one.
        offered = ports(json.loads(self.pactl(["-f", "json", "list", "cards"], deadline) or "[]"))
        if not any(port["card"] == args.get("card") and port["profile"] == args.get("profile") for port in offered):
            raise ValueError("unknown-port")
        self.pactl(["set-card-profile", args["card"], args["profile"]], deadline)
        return dict(done=True)
