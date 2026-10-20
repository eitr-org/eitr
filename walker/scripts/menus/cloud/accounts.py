#!/usr/bin/env python3
"""Add and name cloud accounts for the Walker cloud menus.

Each account is the provider CLI's own unit, created under a name you choose: an
AWS profile, a gcloud configuration, or an Azure subscription. Friendly names
live in the machine-local ~/.config/eitr/cloud-contexts.json. Global CLI
defaults (the default AWS profile, the active gcloud configuration, the
default Azure subscription) are never switched.
"""
import argparse
import configparser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

for _eitr_parent in Path(__file__).resolve().parents:
    _eitr_lib = _eitr_parent / "lib"
    if not (_eitr_lib / "eitr_paths.py").is_file():
        _eitr_lib = _eitr_parent / "distro/lib"
    if (_eitr_lib / "eitr_paths.py").is_file():
        sys.path.insert(0, str(_eitr_lib))
        break
from eitr_forms import Terminal
from eitr_paths import code, config, read_settings, write_settings
from eitr_i18n import tr

PROVIDERS = {"aws": "AWS", "gcp": "Google Cloud", "azure": "Azure"}
# Provider CLI and the package that provides it.
CLIS = {"aws": ("aws", "pacman", "aws-cli-v2"), "gcp": ("gcloud", "aur", "google-cloud-cli"),
        "azure": ("az", "pacman", "azure-cli")}
ui = Terminal()


def names_path():
    return config("eitr/cloud-contexts.json")


def names(provider):
    return read_settings(names_path()).get(provider, {})


def set_name(provider, identifier, label):
    """Store a friendly name, keeping the other providers' names."""
    settings = read_settings(names_path())
    provider_names = dict(settings.get(provider, {}))
    provider_names[identifier] = label
    write_settings(names_path(), {provider: provider_names})


def clean_label(value):
    value = " ".join(value.split())
    if not value or len(value) > 60 or any(ord(character) < 32 for character in value):
        raise ValueError(tr('Use a name of 1 to 60 characters'))
    return value


def slug(label):
    value = re.sub(r"[^a-z0-9]+", "-", label.casefold()).strip("-")
    if not value:
        raise ValueError(tr('The name needs at least one letter or digit'))
    return value[:48]


def identifier(value):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,47}", value):
        raise ValueError(tr('Use lowercase letters, digits and dashes'))
    return value


def aws_profiles():
    """Profile names from the AWS config and credentials files, as the AWS CLI reads them.

    Read directly: `aws configure list-profiles` takes about two seconds to start,
    which would stall the AWS menu on every open.
    """
    home = Path.home()
    sources = ((Path(os.environ.get("AWS_CONFIG_FILE") or home / ".aws/config"), True),
               (Path(os.environ.get("AWS_SHARED_CREDENTIALS_FILE") or home / ".aws/credentials"), False))
    profiles = []
    for path, prefixed in sources:
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        try:
            parser.read(path)
        except configparser.Error:
            continue
        for section in parser.sections():
            # The config file names profiles "profile NAME" (except default) and also
            # holds "sso-session NAME" and "services NAME" sections, which are not profiles.
            if prefixed and section != "default":
                if not section.startswith("profile "):
                    continue
                section = section[len("profile "):]
            name = section.strip()
            if name and name not in profiles:
                profiles.append(name)
    return profiles


def aws_choices():
    """'Label<TAB>profile' lines for the AWS menus."""
    labels = names("aws")
    return [f"{labels.get(profile, profile)}\t{profile}" for profile in aws_profiles()]


def aws_cli_v1():
    """Arch's aws-cli package is version 1, which has no SSO; aws-cli-v2 replaces it."""
    result = subprocess.run(["aws", "--version"], capture_output=True, text=True)
    return (result.stdout + result.stderr).startswith("aws-cli/1.")


def ensure_cli(provider):
    """Offer to install a missing (or, for AWS, too old) provider CLI; False when it stays unusable."""
    command, source, package = CLIS[provider]
    if shutil.which(command) and not (provider == "aws" and aws_cli_v1()):
        return True
    if shutil.which(command):
        print(ui.title(tr('AWS sign-in needs AWS CLI version 2')))
        print(ui.dim(tr('  Version 1 is installed; it has no SSO. pacman asks to remove aws-cli: answer y.')))
    else:
        print(ui.title(tr('{provider_name} needs the {command} command', provider_name=f'{PROVIDERS[provider]}', command=f'{command}')))
    if not ui.confirm(tr('Install {package} now?', package=f'{package}')):
        return False
    sys.path.insert(0, str(code("walker/scripts/actions/install")))
    import software
    software.install(source, [package])
    return bool(shutil.which(command)) and not (provider == "aws" and aws_cli_v1())


def add_aws():
    print(ui.title(tr('Add an AWS account')))
    label = clean_label(ui.ask(tr('Name'), hint=tr('Shown in the AWS menu, for example Acme Production')))
    profile = identifier(ui.ask(tr('Profile ID'), slug(label), tr('The AWS CLI profile name')) or slug(label))
    if profile in aws_profiles():
        raise ValueError(tr('The AWS profile {profile} already exists; rename it with Ctrl+R in the AWS menu', profile=f'{profile}'))
    method = ui.choose(tr('Sign-in method'), [tr('AWS SSO (IAM Identity Center)'), tr('Access keys')])
    print()
    if method == 0:
        print(ui.dim(tr('  The AWS CLI asks for the SSO start URL and region, opens your browser to sign')))
        print(ui.dim(tr('  in, then lists the accounts and roles you can choose from.')))
        command = ["aws", "configure", "sso", "--profile", profile]
    else:
        print(ui.dim(tr('  The AWS CLI asks for the access key ID, secret access key, region and output.')))
        command = ["aws", "configure", "--profile", profile]
    subprocess.run(command, check=True)
    if profile not in aws_profiles():
        raise ValueError(tr('The AWS CLI did not create the profile {profile}', profile=f'{profile}'))
    set_name("aws", profile, label)
    print(ui.ok(tr('{label} is ready in the AWS menu (profile {profile}).', label=f'{label}', profile=f'{profile}')))


def gcp(configuration, *arguments, capture=False):
    """Run gcloud against one named configuration without activating it."""
    environment = dict(os.environ, CLOUDSDK_ACTIVE_CONFIG_NAME=configuration)
    for key in ("CLOUDSDK_CORE_ACCOUNT", "CLOUDSDK_CORE_PROJECT"):
        environment.pop(key, None)
    return subprocess.run(["gcloud", *arguments], env=environment, check=True,
                          capture_output=capture, text=True)


def add_gcp():
    print(ui.title(tr('Add a Google Cloud account')))
    label = clean_label(ui.ask(tr('Name'), hint=tr('Shown in the GCP menu, for example Acme Development')))
    configuration = identifier(ui.ask(tr('Configuration ID'), slug(label), tr('The gcloud configuration name')) or slug(label))
    existing = subprocess.run(["gcloud", "config", "configurations", "list", "--format=value(name)"],
                              capture_output=True, text=True, check=True).stdout.split()
    if configuration in existing:
        raise ValueError(tr('The gcloud configuration {configuration} already exists; rename it with Ctrl+R', configuration=f'{configuration}'))
    subprocess.run(["gcloud", "config", "configurations", "create", configuration, "--no-activate"], check=True)
    print(ui.dim(tr('\n  Your browser opens to sign in.\n')))
    gcp(configuration, "auth", "login")
    projects = json.loads(gcp(configuration, "projects", "list", "--format=json", capture=True).stdout)
    if projects:
        choices = [f"{row['projectId']}  {ui.dim(row.get('name', ''))}" for row in projects]
        project = projects[ui.choose(tr('Project'), choices)]["projectId"]
        gcp(configuration, "config", "set", "project", project)
    set_name("gcp", configuration, label)
    print(ui.ok(tr('{label} is ready in the GCP menu (configuration {configuration}).', label=f'{label}', configuration=f'{configuration}')))


def az(*arguments):
    return json.loads(subprocess.run(["az", *arguments, "--output=json"], capture_output=True, text=True,
                                     check=True).stdout or "null")


def add_azure():
    print(ui.title(tr('Add an Azure account')))
    tenant = ui.ask(tr('Tenant ID or domain'), "Enter for your home tenant")
    try:
        previous = az("account", "show")["id"]
    except (subprocess.CalledProcessError, TypeError, KeyError):
        previous = None
    print(ui.dim(tr('\n  Your browser opens to sign in.\n')))
    subprocess.run(["az", "login", *(["--tenant", tenant] if tenant else [])], check=True,
                   stdout=subprocess.DEVNULL)
    # az login selects a default subscription; restore the one that was active.
    if previous:
        subprocess.run(["az", "account", "set", "--subscription", previous], check=False)
    subscriptions = [row for row in az("account", "list", "--refresh") if row.get("state") == "Enabled"]
    if not subscriptions:
        raise ValueError(tr('This sign-in has no enabled subscriptions'))
    labels = names("azure")
    print(ui.title(tr('Name the subscriptions you want in the menu')))
    print(ui.dim(tr('  Press Enter to keep the shown name.')))
    for row in subscriptions:
        current = labels.get(row["id"], row["name"])
        label = ui.ask(row["name"], current)
        set_name("azure", row["id"], clean_label(label or current))
    print(ui.ok(tr('{subscription_count} subscription(s) are ready in the Azure menu.', subscription_count=f'{len(subscriptions)}')))


def rename(provider, context):
    if provider == "aws" and context not in aws_profiles():
        raise ValueError('Unknown AWS profile')
    current = names(provider).get(context, context)
    print(ui.title(tr('Rename {current}', current=f'{current}')))
    label = ui.ask(tr('New name'), current)
    if label:
        set_name(provider, context, clean_label(label))
        print(ui.ok(tr('Renamed to {label}.', label=f'{label}')))


def main(arguments):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=("add", "rename", "aws-choices"))
    parser.add_argument("provider", nargs="?", choices=tuple(PROVIDERS))
    parser.add_argument("context", nargs="?")
    args = parser.parse_args(arguments)
    if args.action == "aws-choices":
        print("\n".join(aws_choices()))
        return 0
    if args.action == "add":
        if ensure_cli(args.provider):
            {"aws": add_aws, "gcp": add_gcp, "azure": add_azure}[args.provider]()
    elif args.action == "rename":
        rename(args.provider, args.context)
    # Task terminals close after success; keep the outcome readable first.
    input(ui.dim(tr('\nPress Enter to close.')))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f"\n\033[1;31m✗\033[0m {error}", file=sys.stderr)
        sys.exit(1)
    except (KeyboardInterrupt, EOFError):
        print(tr('\nCancelled.'))
        sys.exit(0)
