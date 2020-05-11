import json
from os.path import dirname, join
from unittest import TestCase

from hubitatmaker.types import Device

with open(join(dirname(__file__), "device_details.json")) as f:
    device_details = json.loads(f.read())


class TestTypes(TestCase):
    def test_device_can_serialize(self) -> None:
        """A device should be serializable."""
        d = Device(device_details["6"])
        self.assertEqual(
            f"{d}",
            '<Device id="6" name="Office Door" type="Generic Z-Wave Contact Sensor">',
        )
