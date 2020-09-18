from subprocess import call, check_output
from hubitatmaker import __version__
from sys import exit
from shutil import rmtree


def init():
    call("poetry install", shell=True)
    call("poetry run pre-commit install", shell=True)


def publish():
    latest_tag = check_output(
        ["git", "describe", "--tags", "--abbrev=0"], encoding="utf-8"
    ).strip()
    pkg_version = f"v{__version__}"

    if latest_tag == pkg_version:
        print("Update the package version before publishing")
        exit(1)

    rmtree("dist")

    call("poetry publish --build", shell=True)
    call(f"git tag {pkg_version}", shell=True)
    call("git push --tags", shell=True)


def test():
    call("poetry run mypy hubitatmaker", shell=True)
    call("poetry run python setup.py test", shell=True)
