#!/usr/bin/env python3
"""Add and name cloud accounts for the Walker cloud menus.

Each account is the provider CLI's own unit, created under a name you choose: an
AWS profile, a gcloud configuration, or an Azure subscription. Friendly names
live in the machine-local ~/.config/eitr/cloud-contexts.json. Global CLI
defaults (the default AWS profile, the active gcloud configuration, the
default Azure subscription) are never switched.
"""
import argparse
from contextlib import contextmanager
import tempfile
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
from eitr_terminal import wait_for_escape
from eitr_paths import code, config, read_settings, write_settings
from eitr_wizard import Step, collect as collect_setup
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


@contextmanager
def staged_provider(provider):
    """Keep vendor writes private until sign-in and all follow-up work succeeds."""
    if provider == 'aws':
        targets = {
            'AWS_CONFIG_FILE': Path(os.environ.get('AWS_CONFIG_FILE', str(Path.home() / '.aws/config'))),
            'AWS_SHARED_CREDENTIALS_FILE': Path(os.environ.get('AWS_SHARED_CREDENTIALS_FILE', str(Path.home() / '.aws/credentials'))),
        }
    else:
        variable, fallback = ('CLOUDSDK_CONFIG', config('gcloud')) if provider == 'gcp' else ('AZURE_CONFIG_DIR', Path.home() / '.azure')
        targets = {variable: Path(os.environ.get(variable, str(fallback)))}
    previous = {variable: os.environ.get(variable) for variable in targets}
    original_home = Path.home()
    if provider == 'aws':
        previous['HOME'] = os.environ.get('HOME')
    with tempfile.TemporaryDirectory(prefix='eitr-signin-') as temporary:
        staged = {}
        originals = {}
        for index, (variable, target) in enumerate(targets.items()):
            destination = Path(temporary) / str(index)
            if any(parent.is_symlink() for parent in (target, *target.parents)):
                raise ValueError(str(target))
            if target.is_dir():
                if any(entry.is_symlink() for entry in target.rglob('*')):
                    raise ValueError(str(target))
                shutil.copytree(target, destination)
                originals.update({entry: (entry.read_bytes(), entry.stat().st_mode & 0o777)
                                  for entry in target.rglob('*') if entry.is_file()})
            elif target.is_file():
                shutil.copy2(target, destination)
                originals[target] = (target.read_bytes(), target.stat().st_mode & 0o777)
            staged[variable] = destination
        try:
            for variable, destination in staged.items():
                os.environ[variable] = str(destination)
            if provider == 'aws':
                os.environ['HOME'] = str(Path(temporary) / 'home')
            yield
            changes = {}
            if provider == 'aws':
                cache = Path(temporary) / 'home/.aws/sso'
                if cache.is_dir():
                    for entry in cache.rglob('*'):
                        if entry.is_symlink():
                            raise ValueError(str(entry))
                        if entry.is_file():
                            target = original_home / '.aws/sso' / entry.relative_to(cache)
                            if target.is_file():
                                originals[target] = (target.read_bytes(), target.stat().st_mode & 0o777)
                            changes[target] = entry.read_bytes()
            for variable, destination in staged.items():
                target = targets[variable]
                if destination.is_file():
                    changes[target] = destination.read_bytes()
                elif destination.is_dir():
                    for entry in destination.rglob('*'):
                        if entry.is_symlink():
                            raise ValueError(str(entry))
                        if entry.is_file():
                            changes[target / entry.relative_to(destination)] = entry.read_bytes()
            for target, (contents, _) in originals.items():
                if not target.is_file() or target.read_bytes() != contents:
                    raise ValueError(tr('Configuration changed during preview: {path}', path=str(target)))
            written, created = [], []
            try:
                for target, contents in changes.items():
                    if target in originals and contents == originals[target][0]:
                        continue
                    if target not in originals and target.exists():
                        raise ValueError(str(target))
                    missing = target.parent
                    parents = []
                    while not missing.exists():
                        parents.append(missing)
                        missing = missing.parent
                    for parent in reversed(parents):
                        parent.mkdir(mode=0o700)
                        created.append(parent)
                    written.append(target)
                    with target.open('wb') as handle:
                        os.chmod(target, originals.get(target, (None, 0o600))[1])
                        handle.write(contents)
            except BaseException:
                for target in reversed(written):
                    if target in originals:
                        target.write_bytes(originals[target][0])
                    else:
                        target.unlink(missing_ok=True)
                for parent in reversed(created):
                    parent.rmdir()
                raise
        finally:
            for variable, value in previous.items():
                if value is None:
                    os.environ.pop(variable, None)
                else:
                    os.environ[variable] = value


def add_aws(check_cli=False):
    answers = collect_setup(tr('Add an AWS account'), [
        Step('label', tr('Name'), validator=lambda value: slug(clean_label(value))),
        Step('profile', tr('Profile ID'), default=lambda values: slug(values['label']) if values.get('label') else '', validator=identifier),
        Step('method', tr('Sign-in method'), options=[
            (tr('AWS SSO (IAM Identity Center)'), 0), (tr('Access keys'), 1)]),
    ])
    if check_cli and not ensure_cli('aws'):
        return
    label, profile, method = (answers[key] for key in ('label', 'profile', 'method'))
    if profile in aws_profiles():
        raise ValueError(tr('The AWS profile {profile} already exists; rename it with Ctrl+R in the AWS menu', profile=profile))
    print()
    if method == 0:
        print(ui.dim(tr('  The AWS CLI asks for the SSO start URL and region, opens your browser to sign')))
        print(ui.dim(tr('  in, then lists the accounts and roles you can choose from.')))
        command = ["aws", "configure", "sso", "--profile", profile]
    else:
        print(ui.dim(tr('  The AWS CLI asks for the access key ID, secret access key, region and output.')))
        command = ["aws", "configure", "--profile", profile]
    with staged_provider('aws'):
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


def add_gcp(check_cli=False):
    answers = collect_setup(tr('Add a Google Cloud account'), [
        Step('label', tr('Name'), validator=lambda value: slug(clean_label(value))),
        Step('configuration', tr('Configuration ID'), default=lambda values: slug(values['label']) if values.get('label') else '', validator=identifier),
        Step('project', tr('Project'), optional=True),
    ])
    if check_cli and not ensure_cli('gcp'):
        return
    label, configuration = answers['label'], answers['configuration']
    existing = subprocess.run(["gcloud", "config", "configurations", "list", "--format=value(name)"],
                              capture_output=True, text=True, check=True).stdout.split()
    if configuration in existing:
        raise ValueError(tr('The gcloud configuration {configuration} already exists; rename it with Ctrl+R', configuration=f'{configuration}'))
    with staged_provider('gcp'):
        subprocess.run(["gcloud", "config", "configurations", "create", configuration, "--no-activate"], check=True)
        print(ui.dim(tr('\n  Your browser opens to sign in.\n')))
        gcp(configuration, "auth", "login")
        if answers['project']:
            gcp(configuration, 'config', 'set', 'project', answers['project'])
    set_name("gcp", configuration, label)
    print(ui.ok(tr('{label} is ready in the GCP menu (configuration {configuration}).', label=f'{label}', configuration=f'{configuration}')))


def az(*arguments):
    return json.loads(subprocess.run(["az", *arguments, "--output=json"], capture_output=True, text=True,
                                     check=True).stdout or "null")


def add_azure(check_cli=False):
    print(ui.title(tr('Add an Azure account')))
    answers = collect_setup(tr('Add an Azure account'), [
        Step('tenant', tr('Tenant ID or domain'), optional=True),
        Step('label', tr('Name'), optional=True, validator=clean_label),
    ])
    if check_cli and not ensure_cli('azure'):
        return
    tenant = answers['tenant']
    with staged_provider('azure'):
        try:
            previous = az("account", "show")["id"]
        except (subprocess.CalledProcessError, TypeError, KeyError):
            previous = None
        print(ui.dim(tr('\n  Your browser opens to sign in.\n')))
        subprocess.run(["az", "login", *(["--tenant", tenant] if tenant else [])], check=True,
                       stdout=subprocess.DEVNULL)
        # az login selects a default subscription; restore the one that was active.
        if previous:
            subprocess.run(["az", "account", "set", "--subscription", previous], check=True)
        subscriptions = [row for row in az("account", "list", "--refresh") if row.get("state") == "Enabled"]
        if not subscriptions:
            raise ValueError(tr('This sign-in has no enabled subscriptions'))
    labels = names("azure")
    print(ui.title(tr('Name the subscriptions you want in the menu')))
    print(ui.dim(tr('  Press Enter to keep the shown name.')))
    for row in subscriptions:
        current = labels.get(row["id"], row["name"])
        label = answers["label"] or current
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
        {"aws": add_aws, "gcp": add_gcp, "azure": add_azure}[args.provider](check_cli=True)
    elif args.action == "rename":
        rename(args.provider, args.context)
    # Task terminals close after success; keep the outcome readable first.
    wait_for_escape()
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
