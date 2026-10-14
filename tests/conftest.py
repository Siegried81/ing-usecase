"""Make the no-network rule enforced instead of promised.

Every test mocks its HTTP, but nothing stopped a new test from reaching the
network by accident: the claim was checked by hand once, which does not survive
the next test someone adds. This fixture blocks outbound sockets for the whole
suite, so a forgotten mock fails loudly here rather than fetching a bank's
website from CI. Loopback stays open, because a local fixture server is not the
network this rule is about.
"""

from __future__ import annotations

import socket

import pytest

_real_connect = socket.socket.connect
_real_connect_ex = socket.socket.connect_ex


def _is_loopback(address: object) -> bool:
    """True for 127.0.0.0/8, ::1 and unix sockets, which are not "the network"."""
    if not isinstance(address, tuple) or not address:
        return True  # unix socket path: nothing leaves the machine
    host = str(address[0])
    return host.startswith("127.") or host in ("localhost", "::1", "")


class NetworkUsedInTests(RuntimeError):
    """A test tried to open a real connection; mock it instead."""


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def guard(self, address, *args, **kwargs):
        if _is_loopback(address):
            return _real_connect(self, address, *args, **kwargs)
        raise NetworkUsedInTests(
            f"a test tried to connect to {address!r}. Tests must mock every HTTP call "
            "(see CLAUDE.md); no test may fetch a real page."
        )

    def guard_ex(self, address, *args, **kwargs):
        if _is_loopback(address):
            return _real_connect_ex(self, address, *args, **kwargs)
        raise NetworkUsedInTests(f"a test tried to connect to {address!r}; mock it instead.")

    monkeypatch.setattr(socket.socket, "connect", guard)
    monkeypatch.setattr(socket.socket, "connect_ex", guard_ex)
