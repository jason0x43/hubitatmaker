import json
from os.path import dirname, join

from hubitatmaker.types import Device

with open(join(dirname(__file__), "device_details.json")) as f:
    device_details = json.loads(f.read())


def test_device_can_serialize() -> None:
    """A device should be serializable."""
    d = Device(device_details["6"])
    assert (
        f"{d}"
        == '<Device id="6" name="Office Door" type="Generic Z-Wave Contact Sensor">'
    )


def test_device_records_last_update_time() -> None:
    """A device should be serializable."""
    d = Device(device_details["6"])
    update = d.last_update
    assert update is not None

    d.update_attr("contact", "closed")
    assert update != d.last_update
