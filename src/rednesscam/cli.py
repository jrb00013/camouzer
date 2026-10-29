"""CLI entrypoint: `rednesscam run`."""

from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="rednesscam",
        description="Reduce facial redness and publish to the RednessCam Windows virtual camera.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="Capture webcam → filter → virtual cam")
    run.add_argument("--camera", type=int, default=1, help="OpenCV camera index (default 1 = Logitech on this PC)")
    run.add_argument(
        "--device-name",
        default=None,
        help="Optional DirectShow/MSMF device name (default: open by --camera index)",
    )
    run.add_argument(
        "--strength",
        type=float,
        default=0.45,
        help="Redness reduction 0..1 (default 0.45)",
    )
    run.add_argument("--preview", action="store_true", help="Show local preview window")
    run.add_argument("--frames", type=int, default=None, help="Optional frame cap (testing)")
    run.add_argument(
        "--test-pattern",
        action="store_true",
        help="Ignore webcam; publish a moving test pattern",
    )
    run.add_argument(
        "--no-fallback",
        action="store_true",
        help="Fail if webcam cannot open (do not use test pattern)",
    )

    sub.add_parser("list-cameras", help="Probe camera indices that open successfully")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "list-cameras":
        from .capture import list_camera_indices

        found = list_camera_indices()
        if not found:
            print("No cameras responded.")
            return 1
        print("Cameras:", ", ".join(str(i) for i in found))
        return 0

    if args.cmd == "run":
        from .pipeline import run_pipeline

        run_pipeline(
            camera_index=args.camera,
            strength=args.strength,
            preview=args.preview,
            max_frames=args.frames,
            test_pattern=args.test_pattern,
            device_name=args.device_name,
            allow_test_fallback=not args.no_fallback,
        )
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
