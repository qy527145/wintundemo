from ctypes import *
from ctypes.wintypes import *

wintun = cdll.LoadLibrary('./wintun.dll')


class GUID(Structure):
    _fields_ = [
        ("Data1", ULONG),
        ("Data2", USHORT),
        ("Data3", USHORT),
        ("Data4", c_ubyte * 8),
    ]


class SP_DEVINFO_DATA(Structure):
    _fields_ = [
        ("cbSize", DWORD),
        ("ClassGuid", GUID),
        ("DevInst", DWORD),
        ("Reserved", ULONG),
    ]


class WINTUN_ADAPTER(Structure):
    _fields_ = [
        ("SwDevice", HANDLE),
        ("DevInfo", HANDLE),
        ("DevInfoData", SP_DEVINFO_DATA),
        ("InterfaceFilename", PWCHAR),
        ("CfgInstanceID", GUID),
        ("DevInstanceID", WCHAR * 10000),
        ("LuidIndex", DWORD),
        ("IfType", DWORD),
        ("IfIndex", DWORD),
    ]


class CRITICAL_SECTION(Structure):
    _fields_ = [
        ("DebugInfo", LPVOID),
        ("LockCount", LONG),
        ("RecursionCount", LONG),
        ("OwningThread", LPVOID),
        ("LockSemaphore", LPVOID),
        ("SpinCount", ULONG),
    ]


class RECEIVE(Structure):
    _fields_ = [
        ("Tail", ULONG),
        ("TailRelease", ULONG),
        ("PacketsToRelease", ULONG),
        ("Lock", CRITICAL_SECTION),
    ]


class SEND(Structure):
    _fields_ = [
        ("Head", ULONG),
        ("HeadRelease", ULONG),
        ("PacketsToRelease", ULONG),
        ("Lock", CRITICAL_SECTION),
    ]


class TUN_RING(Structure):
    _fields_ = [
        ("Head", ULONG),
        ("Tail", ULONG),
        ("Alertable", ULONG),
        ("Data", POINTER(c_ubyte)),
    ]


class TUN_RING_TMP(Structure):
    _fields_ = [
        ("RingSize", ULONG),
        ("Ring", POINTER(TUN_RING)),
        ("TailMoved", HANDLE),
    ]


class TUN_REGISTER_RINGS(Structure):
    _fields_ = [
        ("Send", TUN_RING_TMP),
        ("Receive", TUN_RING_TMP),
    ]


class SESSION(Structure):
    _fields_ = [
        ("Capacity", ULONG),
        ("Receive", RECEIVE),
        ("Send", SEND),
        ("Descriptor", TUN_REGISTER_RINGS),
        ("Handle", HANDLE),
    ]


##########################################################
WintunCreateAdapter = wintun.WintunCreateAdapter
WintunCreateAdapter.restype = HANDLE
WintunCreateAdapter.argtypes = [LPCWSTR, LPCWSTR, LPVOID]

##########################################################
WintunOpenAdapter = wintun.WintunOpenAdapter
WintunOpenAdapter.restype = HANDLE
WintunOpenAdapter.argtypes = [LPCWSTR]

##########################################################
WintunCloseAdapter = wintun.WintunCloseAdapter
WintunCloseAdapter.argtypes = [HANDLE]

##########################################################
WintunDeleteDriver = wintun.WintunDeleteDriver

##########################################################
WintunStartSession = wintun.WintunStartSession
WintunStartSession.restype = POINTER(SESSION)
WintunStartSession.restype = HANDLE
WintunStartSession.argtypes = [HANDLE, DWORD]

##########################################################
WintunEndSession = wintun.WintunEndSession
WintunEndSession.argtypes = [HANDLE]

##########################################################
WintunAllocateSendPacket = wintun.WintunAllocateSendPacket
WintunAllocateSendPacket.restype = PBYTE
WintunAllocateSendPacket.argtypes = [HANDLE, DWORD]

##########################################################
WintunSendPacket = wintun.WintunSendPacket
WintunSendPacket.argtypes = [HANDLE, PBYTE]

##########################################################
WintunReceivePacket = wintun.WintunReceivePacket
WintunReceivePacket.restype = PBYTE
WintunReceivePacket.argtypes = [HANDLE, PDWORD]

##########################################################
WintunReleaseReceivePacket = wintun.WintunReleaseReceivePacket
WintunReleaseReceivePacket.argtypes = [HANDLE, PBYTE]


##########################################################


class WinTun:
    def __init__(self):
        self.adapter = WintunCreateAdapter(LPCWSTR('demo'), LPCWSTR('Wintun'), None)
        self.session = WintunStartSession(self.adapter, 0x400000)

    def open(self, name):
        self.adapter = WintunCreateAdapter(LPCWSTR(name), )
        pass

    def send(self, data):
        size = DWORD(len(data))
        p_data = WintunAllocateSendPacket(self.session, size)
        a_data = (BYTE * size.value).from_address(addressof(p_data.contents))
        a_data[:] = data
        WintunSendPacket(self.session, p_data)

    def recv(self):
        size = DWORD(0)
        p_data = WintunReceivePacket(self.session, pointer(size))
        if size.value == 0:
            return b''
        a_data = (BYTE * size.value).from_address(addressof(p_data.contents))
        data = bytes([i if i >= 0 else 128 + i for i in a_data[:]])
        # data = string_at(p_data)
        WintunReleaseReceivePacket(self.session, p_data)
        return data

    def close(self):
        WintunEndSession(self.session)
        WintunCloseAdapter(self.adapter)
        WintunDeleteDriver()


if __name__ == '__main__':
    obj = WinTun()
    obj.send(bytes.fromhex(
        """
46 00 00 28 28 dd 00 00 01 02 df b8 c0 a8 7b 7b
e0 00 00 16 94 04 00 00 22 00 f9 01 00 00 00 01
04 00 00 00 e0 00 00 fc
        """))
    count = 0
    while True:
        data = obj.recv()
        if len(data) == 0:
            break
        count += len(data)
    obj.close()
    pass
