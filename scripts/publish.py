from subprocess import call, check_output
from hubitatmaker import __version__
from sys import exit
from shutil import rmtree
import toml


latest_tag = check_output(
    ["git", "describe", "--tags", "--abbrev=0"], encoding="utf-8"
).strip()
pkg_version = f"v{__version__}"
proj_version = f"v{toml.load('pyproject.toml')['project']['version']}"

if pkg_version != proj_version:
    print(
        f"Package version ({pkg_version}) different from project version ({proj_version})"
    )
    exit(1)

if latest_tag == pkg_version:
    print("Update the package version before publishing")
    exit(1)

rmtree("dist")

call("pdm build", shell=True)
call("twine upload -r testpypi dist/*", shell=True)
call(f"git tag {pkg_version}", shell=True)
#call("git push --tags", shell=True)
