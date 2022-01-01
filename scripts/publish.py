from subprocess import call, check_output
from hubitatmaker import __version__
from sys import exit
from shutil import rmtree


latest_tag = check_output(
    ["git", "describe", "--tags", "--abbrev=0"], encoding="utf-8"
).strip()
pkg_version = f"v{__version__}"

if latest_tag == pkg_version:
    print("Update the package version before publishing")
    exit(1)

rmtree("dist")

if call("pdm build", shell=True):
    exit(1)

# set TWINE_REPOSITORY to testpypi for test publishing
if call("twine upload dist/*", shell=True):
    exit(1)

if call(f"git tag {pkg_version}", shell=True):
    exit(1)

if call("git push", shell=True):
    exit(1)

if call("git push --tags", shell=True):
    exit(1)
