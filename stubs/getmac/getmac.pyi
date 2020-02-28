from typing import Any, Optional

log: Any
PY2: Any
DEBUG: int
PORT: int
WINDOWS: Any
DARWIN: Any
OPENBSD: Any
FREEBSD: Any
BSD: Any
WSL: bool
LINUX: bool
PATH: Any
ENV: Any
IP4: int
IP6: int
INTERFACE: int
HOSTNAME: int
MAC_RE_COLON: str
MAC_RE_DASH: str
MAC_RE_DARWIN: str
WARNED_PY2: bool

def get_mac_address(interface: Optional[str]=..., ip: Optional[str]=..., ip6: Optional[str]=..., hostname: Optional[str]=..., network_request: bool=...) -> Optional[str]: ...
