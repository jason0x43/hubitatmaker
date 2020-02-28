from typing import Any, Dict, List, Mapping, Optional, Tuple, Union
from types import MappingProxyType


class Attribute:
    def __init__(self, properties: Dict[str, Any]):
        self._properties = properties

    @property
    def name(self) -> str:
        return self._properties["name"]

    @property
    def type(self) -> str:
        return self._properties["dataType"]

    @property
    def value(self) -> Union[str, float]:
        return self._properties["currentValue"]

    @property
    def values(self) -> Optional[List[str]]:
        if "values" not in self._properties:
            return None
        return self._properties["values"]

    def update_value(self, value: Union[str, float]) -> None:
        self._properties["currentValue"] = value

    def __iter__(self):
        for key in "name", "type", "value":
            yield key, getattr(self, key)

    def __str__(self):
        return f"<Attribute name={self.name} type={self.type} value={self.value}>"


class Device:
    def __init__(self, properties: Dict[str, Any]):
        self.update_state(properties)

    @property
    def id(self) -> str:
        return self._properties["id"]

    @property
    def name(self) -> str:
        return self._properties["label"]

    @property
    def type(self) -> str:
        return self._properties["name"]

    @property
    def attributes(self) -> Mapping[str, Attribute]:
        return self._attributes_ro

    @property
    def capabilities(self) -> Tuple[str, ...]:
        return self._capabilities

    def update_state(self, properties: Dict[str, Any]):
        self._properties = properties

        self._attributes: Dict[str, Attribute] = {}
        self._attributes_ro = MappingProxyType(self._attributes)
        for attr in properties.get("attributes", []):
            self._attributes[attr["name"]] = Attribute(attr)

        caps: List[str] = [
            p for p in properties.get("capabilities", []) if isinstance(p, str)
        ]
        self._capabilities: Tuple[str, ...] = tuple(caps)

    def __iter__(self):
        for key in "id", "name", "type", "attributes", "capabilities":
            yield key, getattr(self, key)

    def __str__(self):
        return f"<Device device_id={self.device_id}>"


class Event:
    def __init__(self, properties: Dict[str, Any]):
        self._properties = properties

    @property
    def device_id(self) -> str:
        return self._properties["deviceId"]

    @property
    def device_name(self) -> Optional[str]:
        return self._properties.get("displayName")

    @property
    def description(self) -> Optional[str]:
        return self._properties.get("descriptionText")

    @property
    def attribute(self) -> str:
        return self._properties["name"]

    @property
    def value(self) -> Union[str, float]:
        return self._properties["value"]

    def __iter__(self):
        for key in "device_id", "device_name", "attribute", "value", "description":
            yield key, getattr(self, key)

    def __str__(self) -> str:
        return f'<Event device_id="{self.device_id}" device_name="{self.device_name}" attribute="{self.attribute}" value="{self.value}" description="{self.description}">'
