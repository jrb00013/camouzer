"""Windows Global shared-memory writer matching RednessCamSource.dll layout."""

from __future__ import annotations

import ctypes
import struct
import time
from ctypes import wintypes

SHARED_MEM_NAME = "Global\\RednessCam_SharedMem"
MUTEX_NAME = "Global\\RednessCam_Mutex"

TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080
FRAME_SIZE = TARGET_WIDTH * TARGET_HEIGHT * 3 // 2
HEADER_SIZE = 24
TOTAL_SIZE = HEADER_SIZE + FRAME_SIZE

FILE_MAP_ALL_ACCESS = 0x000F001F
WAIT_OBJECT_0 = 0
INFINITE = 0xFFFFFFFF


class SharedMemoryWriter:
    """Push NV12 frames into the RednessCam FrameServer shared mapping."""

    def __init__(self, timeout_s: float = 60.0) -> None:
        self._k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._k32.OpenFileMappingW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
        self._k32.OpenFileMappingW.restype = wintypes.HANDLE
        self._k32.MapViewOfFile.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.c_size_t,
        ]
        self._k32.MapViewOfFile.restype = wintypes.LPVOID
        self._k32.OpenMutexW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
        self._k32.OpenMutexW.restype = wintypes.HANDLE
        self._k32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self._k32.WaitForSingleObject.restype = wintypes.DWORD
        self._k32.ReleaseMutex.argtypes = [wintypes.HANDLE]
        self._k32.ReleaseMutex.restype = wintypes.BOOL
        self._k32.UnmapViewOfFile.argtypes = [wintypes.LPCVOID]
        self._k32.CloseHandle.argtypes = [wintypes.HANDLE]

        self._h_map = None
        self._h_mutex = None
        self._ptr = None
        self._frame_index = 0
        self._connect(timeout_s)

    def _connect(self, timeout_s: float) -> None:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            h_map = self._k32.OpenFileMappingW(FILE_MAP_ALL_ACCESS, False, SHARED_MEM_NAME)
            if h_map:
                self._h_map = h_map
                break
            time.sleep(0.25)
        if not self._h_map:
            raise RuntimeError(
                "Could not open Global\\RednessCam_SharedMem. "
                "Start RednessCamHost.exe (as Administrator after regsvr32) first."
            )

        ptr = self._k32.MapViewOfFile(self._h_map, FILE_MAP_ALL_ACCESS, 0, 0, TOTAL_SIZE)
        if not ptr:
            raise RuntimeError("MapViewOfFile failed for RednessCam shared memory.")
        self._ptr = ptr

        # Mutex is optional but preferred.
        SYNCHRONIZE = 0x00100000
        MUTEX_ALL = 0x1F0001
        self._h_mutex = self._k32.OpenMutexW(MUTEX_ALL | SYNCHRONIZE, False, MUTEX_NAME)

        # Stamp expected dimensions for consumers.
        header = struct.pack(
            "<4IQ",
            TARGET_WIDTH,
            TARGET_HEIGHT,
            TARGET_WIDTH,
            FRAME_SIZE,
            0,
        )
        ctypes.memmove(self._ptr, header, HEADER_SIZE)

    def write_nv12(self, nv12: bytes | memoryview) -> None:
        if len(nv12) != FRAME_SIZE:
            raise ValueError(f"NV12 size must be {FRAME_SIZE}, got {len(nv12)}")
        if self._h_mutex:
            self._k32.WaitForSingleObject(self._h_mutex, 50)
        try:
            self._frame_index += 1
            header = struct.pack(
                "<4IQ",
                TARGET_WIDTH,
                TARGET_HEIGHT,
                TARGET_WIDTH,
                FRAME_SIZE,
                self._frame_index,
            )
            ctypes.memmove(self._ptr, header, HEADER_SIZE)
            ctypes.memmove(self._ptr + HEADER_SIZE, bytes(nv12), FRAME_SIZE)
        finally:
            if self._h_mutex:
                self._k32.ReleaseMutex(self._h_mutex)

    def close(self) -> None:
        if self._ptr:
            self._k32.UnmapViewOfFile(self._ptr)
            self._ptr = None
        if self._h_map:
            self._k32.CloseHandle(self._h_map)
            self._h_map = None
        if self._h_mutex:
            self._k32.CloseHandle(self._h_mutex)
            self._h_mutex = None

    def __enter__(self) -> "SharedMemoryWriter":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
