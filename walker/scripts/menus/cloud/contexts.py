#!/usr/bin/env python3
"""Discover cloud contexts and launch tools without changing CLI defaults."""
import argparse
import base64
import configparser
import json
import os
from pathlib import Path

import sys
for _eitr_parent in Path(__file__).resolve().parents:
    _eitr_lib = _eitr_parent / "lib"
    if not (_eitr_lib / "eitr_paths.py").is_file():
        _eitr_lib = _eitr_parent / "distro/lib"
    if (_eitr_lib / "eitr_paths.py").is_file():
        sys.path.insert(0, str(_eitr_lib))
        break
from eitr_paths import code, config as user_config, read_settings
from eitr_i18n import tr
import re
import shlex
import subprocess

CONFIG = user_config()


def query(command):
    result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=True)
    return json.loads(result.stdout)


def gcloud_configurations():
    """Read gcloud's named configurations directly; starting the CLI takes about a second."""
    directory = Path(os.environ.get("CLOUDSDK_CONFIG") or user_config("gcloud")) / "configurations"
    for path in sorted(directory.glob("config_*")):
        parser = configparser.ConfigParser(interpolation=None)
        try:
            parser.read(path)
        except configparser.Error:
            continue
        core = dict(parser["core"]) if parser.has_section("core") else {}
        yield {"name": path.name.removeprefix("config_"), "properties": {"core": core}}


def azure_subscriptions():
    """Read the Azure CLI's cached subscriptions directly; starting az takes about a second."""
    directory = Path(os.environ.get("AZURE_CONFIG_DIR") or Path.home() / ".azure")
    try:
        profile = json.loads((directory / "azureProfile.json").read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return []
    settings = configparser.ConfigParser(interpolation=None)
    try:
        settings.read(directory / "config")
    except configparser.Error:
        pass
    # Like az account list, show only the active cloud's subscriptions.
    cloud = settings.get("cloud", "name", fallback="AzureCloud")
    return [row for row in profile.get("subscriptions", [])
            if row.get("environmentName", "AzureCloud") == cloud]


def contexts(provider):
    aliases_path = CONFIG / "eitr/cloud-contexts.json"
    aliases = read_settings(aliases_path).get(provider, {})
    if provider == "gcp":
        result = []
        for row in gcloud_configurations():
            core = row.get("properties", {}).get("core", {})
            if not core.get("account"):
                continue
            result.append({"configuration": row["name"], "account": core["account"],
                           "project": core.get("project") or "", "label": aliases.get(row["name"], row["name"])})
        return result
    return [{"subscription": row["id"], "tenant": row["tenantId"],
             "label": aliases.get(row["id"], row["name"])}
            for row in azure_subscriptions()
            if row.get("state") == "Enabled"]


def title(context):
    detail = " · ".join(context[key] for key in ("account", "project", "tenant", "subscription") if context.get(key))
    return context["label"] + " — " + detail


def environment(provider, context):
    values = {"EITR_CLOUD_CONTEXT": title(context)}
    if provider == "gcp":
        if context.get("project") and not re.fullmatch(r"[a-z][a-z0-9-]{4,61}[a-z0-9]", context["project"]):
            raise ValueError(tr('Invalid project ID'))
        values.update(CLOUDSDK_ACTIVE_CONFIG_NAME=context["configuration"], CLOUDSDK_CORE_ACCOUNT=context["account"])
        # An empty CLOUDSDK_CORE_PROJECT would unset the configuration's project instead of leaving it alone.
        if context.get("project"):
            values["CLOUDSDK_CORE_PROJECT"] = context["project"]
    else:
        if not re.fullmatch(r"[a-fA-F0-9-]{36}", context["subscription"]):
            raise ValueError(tr('Invalid subscription ID'))
        values["EITR_AZURE_SUBSCRIPTION"] = context["subscription"]
        if not re.fullmatch(r"[a-fA-F0-9-]{36}", context["tenant"]):
            raise ValueError(tr('Invalid tenant ID'))
        values["EITR_AZURE_TENANT"] = context["tenant"]
    values["EITR_CLOUD_CONTEXT"] = title(context)
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("provider", choices=("gcp", "azure"))
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--open")
    parser.add_argument("--shell", action="store_true")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    if args.refresh:
        if args.provider == "azure":
            query(["az", "account", "list", "--refresh", "--output=json"])
        subprocess.run([str(code("walker/bin/walker")), "--provider", "menus:" + args.provider + "-contexts"], check=True)
        return
    rows = contexts(args.provider)
    if args.list:
        for row in sorted(rows, key=lambda row: row["label"].casefold()):
            token = base64.urlsafe_b64encode(json.dumps(row).encode()).decode()
            # The third column is the ID that friendly names are stored under.
            key = row.get("configuration") or row.get("subscription")
            print(title(row).replace("\n", " ").replace("\t", " ") + "\t" + token + "\t" + key)
        return
    if args.open:
        selected = json.loads(base64.urlsafe_b64decode(args.open))
        if selected not in rows:
            raise ValueError(tr('Context changed; refresh the menu'))
    else:
        import navigation
        navigation.show(args.provider + '-contexts')
        return
    if args.shell:
        values = environment(args.provider, selected)
        if args.provider == 'gcp' and 'CLOUDSDK_CORE_PROJECT' not in values:
            print('unset CLOUDSDK_CORE_PROJECT')
        print("\n".join("export " + key + "=" + shlex.quote(value) for key, value in values.items()))
    else:
        import navigation
        navigation.select(args.provider, selected)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        if "--list" not in sys.argv:
            subprocess.run(["notify-send", tr('Cloud'), str(error)], check=False)
        sys.exit(1)
