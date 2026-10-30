"""FFmpeg dshow capture — forces MJPG 720p@30 when OpenCV won't."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import numpy as np


def find_ffmpeg() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found

    # Winget / local installs under the current user (no hardcoded username).
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        winget = Path(local) / "Microsoft" / "WinGet" / "Packages"
        if winget.is_dir():
            matches = sorted(winget.glob("**/ffmpeg.exe"))
            if matches:
                return str(matches[-1])

    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    for candidate in (
        Path(pf) / "ffmpeg" / "bin" / "ffmpeg.exe",
        Path(pf) / "Gyan" / "ffmpeg" / "bin" / "ffmpeg.exe",
    ):
        if candidate.is_file():
            return str(candidate)

    raise RuntimeError(
        "ffmpeg not found on PATH (or under LOCALAPPDATA\\Microsoft\\WinGet\\Packages). "
        "Install ffmpeg, then retry."
    )


class FFmpegCamera:
    """Read BGR frames from ffmpeg dshow MJPG."""

    def __init__(
        self,
        device_name: str = "Logitech Webcam C930e",
        width: int = 1280,
        height: int = 720,
        fps: int = 30,
    ) -> None:
        self.width = width
        self.height = height
        self.fps = fps
        self.frame_bytes = width * height * 3
        ff = find_ffmpeg()
        cmd = [
            ff,
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "dshow",
            "-video_size",
            f"{width}x{height}",
            "-framerate",
            str(fps),
            "-vcodec",
            "mjpeg",
            "-i",
            f"video={device_name}",
            "-an",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "bgr24",
            "-s",
            f"{width}x{height}",
            "-r",
            str(fps),
            "pipe:1",
        ]
        print(f"[camouzer] ffmpeg capture: {device_name} {width}x{height}@{fps} mjpeg", flush=True)
        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=self.frame_bytes * 2,
        )

    def read(self):
        assert self._proc.stdout is not None
        raw = self._proc.stdout.read(self.frame_bytes)
        if not raw or len(raw) < self.frame_bytes:
            return False, None
        frame = np.frombuffer(raw, dtype=np.uint8).reshape((self.height, self.width, 3))
        return True, frame

    def release(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        self._proc = None  # type: ignore

    def isOpened(self) -> bool:
        return self._proc is not None and self._proc.poll() is None
