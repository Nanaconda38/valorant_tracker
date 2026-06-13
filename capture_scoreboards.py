import argparse
import csv
import ctypes
import datetime as dt
import platform
import struct
import sys
import time
from dataclasses import dataclass
from pathlib import Path


MOD_NOREPEAT = 0x4000
VK_NUMPAD0 = 0x60
VK_ESCAPE = 0x1B
HOTKEY_CAPTURE_ID = 1
HOTKEY_EXIT_ID = 2
WM_HOTKEY = 0x0312
SRCCOPY = 0x00CC0020
BI_RGB = 0
PS_SOLID = 0
NULL_BRUSH = 5
RDW_INVALIDATE = 0x0001
RDW_ERASE = 0x0004
RDW_ALLCHILDREN = 0x0080
RDW_UPDATENOW = 0x0100

SM_CXSCREEN = 0
SM_CYSCREEN = 1
SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79


@dataclass(frozen=True)
class Region:
    x: int
    y: int
    width: int
    height: int

    def label(self) -> str:
        return f"{self.x},{self.y},{self.width},{self.height}"


class POINT(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_long),
        ("y", ctypes.c_long),
    ]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", ctypes.c_void_p),
        ("message", ctypes.c_uint),
        ("wParam", ctypes.c_size_t),
        ("lParam", ctypes.c_ssize_t),
        ("time", ctypes.c_uint),
        ("pt", POINT),
    ]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", ctypes.c_uint32),
        ("biWidth", ctypes.c_int32),
        ("biHeight", ctypes.c_int32),
        ("biPlanes", ctypes.c_uint16),
        ("biBitCount", ctypes.c_uint16),
        ("biCompression", ctypes.c_uint32),
        ("biSizeImage", ctypes.c_uint32),
        ("biXPelsPerMeter", ctypes.c_int32),
        ("biYPelsPerMeter", ctypes.c_int32),
        ("biClrUsed", ctypes.c_uint32),
        ("biClrImportant", ctypes.c_uint32),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", ctypes.c_uint32 * 3),
    ]


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


def ensure_windows() -> tuple[ctypes.CDLL, ctypes.CDLL]:
    if platform.system() != "Windows":
        raise RuntimeError(
            "Screen capture uses Win32 APIs. Run this script with Windows Python "
            "from PyCharm/PowerShell, not from WSL."
        )

    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    user32.GetSystemMetrics.argtypes = [ctypes.c_int]
    user32.GetSystemMetrics.restype = ctypes.c_int
    user32.GetDC.argtypes = [ctypes.c_void_p]
    user32.GetDC.restype = ctypes.c_void_p
    user32.ReleaseDC.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    user32.ReleaseDC.restype = ctypes.c_int
    user32.RegisterHotKey.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_uint, ctypes.c_uint]
    user32.RegisterHotKey.restype = ctypes.c_bool
    user32.UnregisterHotKey.argtypes = [ctypes.c_void_p, ctypes.c_int]
    user32.UnregisterHotKey.restype = ctypes.c_bool
    user32.GetMessageW.argtypes = [ctypes.POINTER(MSG), ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint]
    user32.GetMessageW.restype = ctypes.c_int
    user32.EnumWindows.argtypes = None
    user32.EnumWindows.restype = ctypes.c_bool
    user32.IsWindowVisible.argtypes = [ctypes.c_void_p]
    user32.IsWindowVisible.restype = ctypes.c_bool
    user32.GetWindowTextLengthW.argtypes = [ctypes.c_void_p]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.GetWindowRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(RECT)]
    user32.GetWindowRect.restype = ctypes.c_bool
    user32.InvalidateRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(RECT), ctypes.c_bool]
    user32.InvalidateRect.restype = ctypes.c_bool
    user32.RedrawWindow.argtypes = [ctypes.c_void_p, ctypes.POINTER(RECT), ctypes.c_void_p, ctypes.c_uint]
    user32.RedrawWindow.restype = ctypes.c_bool

    gdi32.CreateCompatibleDC.argtypes = [ctypes.c_void_p]
    gdi32.CreateCompatibleDC.restype = ctypes.c_void_p
    gdi32.CreateCompatibleBitmap.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    gdi32.CreateCompatibleBitmap.restype = ctypes.c_void_p
    gdi32.SelectObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    gdi32.SelectObject.restype = ctypes.c_void_p
    gdi32.BitBlt.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_uint,
    ]
    gdi32.BitBlt.restype = ctypes.c_bool
    gdi32.GetDIBits.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_uint,
        ctypes.c_uint,
        ctypes.c_void_p,
        ctypes.POINTER(BITMAPINFO),
        ctypes.c_uint,
    ]
    gdi32.GetDIBits.restype = ctypes.c_int
    gdi32.CreatePen.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint]
    gdi32.CreatePen.restype = ctypes.c_void_p
    gdi32.GetStockObject.argtypes = [ctypes.c_int]
    gdi32.GetStockObject.restype = ctypes.c_void_p
    gdi32.Rectangle.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    gdi32.Rectangle.restype = ctypes.c_bool
    gdi32.GdiFlush.argtypes = []
    gdi32.GdiFlush.restype = ctypes.c_bool
    gdi32.DeleteObject.argtypes = [ctypes.c_void_p]
    gdi32.DeleteObject.restype = ctypes.c_bool
    gdi32.DeleteDC.argtypes = [ctypes.c_void_p]
    gdi32.DeleteDC.restype = ctypes.c_bool

    return user32, gdi32


def screenshot_path(output_dir: Path, prefix: str) -> Path:
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    return output_dir / f"{prefix}_{timestamp}.bmp"


def virtual_screen_region(user32: ctypes.CDLL) -> Region:
    return Region(
        user32.GetSystemMetrics(SM_XVIRTUALSCREEN),
        user32.GetSystemMetrics(SM_YVIRTUALSCREEN),
        user32.GetSystemMetrics(SM_CXVIRTUALSCREEN),
        user32.GetSystemMetrics(SM_CYVIRTUALSCREEN),
    )


def primary_screen_region(user32: ctypes.CDLL) -> Region:
    return Region(
        0,
        0,
        user32.GetSystemMetrics(SM_CXSCREEN),
        user32.GetSystemMetrics(SM_CYSCREEN),
    )


def parse_region(value: str) -> Region:
    try:
        x, y, width, height = [int(part.strip()) for part in value.split(",", 3)]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Region must be formatted as x,y,width,height.") from exc

    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("Region width and height must be greater than zero.")
    return Region(x, y, width, height)


def find_window_region(user32: ctypes.CDLL, title_query: str) -> tuple[Region, str]:
    query = title_query.lower()
    found: dict[str, object] = {}

    enum_windows_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def callback(hwnd: ctypes.c_void_p, _lparam: ctypes.c_void_p) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True

        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True

        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        title = buffer.value.strip()
        if query not in title.lower():
            return True

        rect = RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return True

        width = rect.right - rect.left
        height = rect.bottom - rect.top
        if width <= 0 or height <= 0:
            return True

        found["region"] = Region(rect.left, rect.top, width, height)
        found["title"] = title
        return False

    callback_ptr = enum_windows_proc(callback)
    user32.EnumWindows.argtypes = [enum_windows_proc, ctypes.c_void_p]
    user32.EnumWindows(callback_ptr, None)
    if "region" not in found:
        raise RuntimeError(
            f"No visible window title contains {title_query!r}. "
            "Run with --list-windows to see the exact titles Windows exposes."
        )
    return found["region"], str(found["title"])


def list_visible_windows(user32: ctypes.CDLL) -> list[tuple[str, Region]]:
    windows: list[tuple[str, Region]] = []
    enum_windows_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def callback(hwnd: ctypes.c_void_p, _lparam: ctypes.c_void_p) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True

        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True

        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        title = buffer.value.strip()
        if not title:
            return True

        rect = RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return True

        width = rect.right - rect.left
        height = rect.bottom - rect.top
        if width <= 0 or height <= 0:
            return True

        windows.append((title, Region(rect.left, rect.top, width, height)))
        return True

    callback_ptr = enum_windows_proc(callback)
    user32.EnumWindows.argtypes = [enum_windows_proc, ctypes.c_void_p]
    user32.EnumWindows(callback_ptr, None)
    return windows


def resolve_target_region(user32: ctypes.CDLL, args: argparse.Namespace) -> tuple[Region, str]:
    if args.region:
        return args.region, "manual-region"
    if args.window_title:
        return find_window_region(user32, args.window_title)
    if args.all_screens:
        return virtual_screen_region(user32), "virtual-desktop"
    return primary_screen_region(user32), "primary-screen"


def capture_region(path: Path, region: Region, user32: ctypes.CDLL, gdi32: ctypes.CDLL) -> None:
    """
    Captures a screen region to a top-down BMP file using Win32 APIs.
    """
    width = region.width
    height = region.height

    screen_dc = user32.GetDC(None)
    memory_dc = gdi32.CreateCompatibleDC(screen_dc)
    bitmap = gdi32.CreateCompatibleBitmap(screen_dc, width, height)
    old_bitmap = gdi32.SelectObject(memory_dc, bitmap)

    try:
        if not gdi32.BitBlt(memory_dc, 0, 0, width, height, screen_dc, region.x, region.y, SRCCOPY):
            raise OSError("BitBlt failed while capturing the screen.")

        row_stride = width * 4
        image_size = row_stride * height
        pixels = ctypes.create_string_buffer(image_size)
        info = BITMAPINFO()
        info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        info.bmiHeader.biWidth = width
        info.bmiHeader.biHeight = -height
        info.bmiHeader.biPlanes = 1
        info.bmiHeader.biBitCount = 32
        info.bmiHeader.biCompression = BI_RGB
        info.bmiHeader.biSizeImage = image_size

        lines = gdi32.GetDIBits(memory_dc, bitmap, 0, height, pixels, ctypes.byref(info), 0)
        if lines != height:
            raise OSError("GetDIBits failed while reading the screen bitmap.")

        file_header_size = 14
        dib_header_size = 40
        pixel_offset = file_header_size + dib_header_size
        file_size = pixel_offset + image_size

        file_header = struct.pack("<2sIHHI", b"BM", file_size, 0, 0, pixel_offset)
        dib_header = struct.pack(
            "<IiiHHIIiiII",
            dib_header_size,
            width,
            -height,
            1,
            32,
            BI_RGB,
            image_size,
            0,
            0,
            0,
            0,
        )
        path.write_bytes(file_header + dib_header + pixels.raw)
    finally:
        gdi32.SelectObject(memory_dc, old_bitmap)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(memory_dc)
        user32.ReleaseDC(None, screen_dc)


def color_ref(red: int, green: int, blue: int) -> int:
    return red | (green << 8) | (blue << 16)


def show_capture_indicator(region: Region, user32: ctypes.CDLL, gdi32: ctypes.CDLL, duration_ms: int) -> None:
    if duration_ms <= 0:
        return

    screen_dc = user32.GetDC(None)
    if not screen_dc:
        return

    pen = gdi32.CreatePen(PS_SOLID, 6, color_ref(0, 255, 120))
    old_pen = None
    old_brush = None
    try:
        old_pen = gdi32.SelectObject(screen_dc, pen)
        old_brush = gdi32.SelectObject(screen_dc, gdi32.GetStockObject(NULL_BRUSH))

        left = region.x
        top = region.y
        right = region.x + region.width
        bottom = region.y + region.height
        gdi32.Rectangle(screen_dc, left, top, right, bottom)

        inset = 10
        if region.width > inset * 2 and region.height > inset * 2:
            gdi32.Rectangle(screen_dc, left + inset, top + inset, right - inset, bottom - inset)

        gdi32.GdiFlush()
        time.sleep(duration_ms / 1000)
        redraw_rect = RECT(left, top, right, bottom)
        user32.InvalidateRect(None, ctypes.byref(redraw_rect), True)
        user32.RedrawWindow(
            None,
            ctypes.byref(redraw_rect),
            None,
            RDW_INVALIDATE | RDW_ERASE | RDW_ALLCHILDREN | RDW_UPDATENOW,
        )
    finally:
        if old_pen:
            gdi32.SelectObject(screen_dc, old_pen)
        if old_brush:
            gdi32.SelectObject(screen_dc, old_brush)
        if pen:
            gdi32.DeleteObject(pen)
        user32.ReleaseDC(None, screen_dc)


def append_index(
    index_path: Path,
    image_path: Path,
    captured_at: dt.datetime,
    mode: str,
    region: Region,
    window_title: str,
    dataset_path: Path,
    note: str,
) -> None:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "captured_at",
        "image_path",
        "mode",
        "window_title",
        "region_x",
        "region_y",
        "region_width",
        "region_height",
        "dataset_path",
        "note",
        "processed",
    ]
    needs_header = not index_path.exists() or index_path.stat().st_size == 0
    try:
        display_image_path = image_path.relative_to(Path.cwd())
    except ValueError:
        display_image_path = image_path

    with index_path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        if needs_header:
            writer.writeheader()
        writer.writerow({
            "captured_at": captured_at.isoformat(timespec="seconds"),
            "image_path": display_image_path.as_posix(),
            "mode": mode,
            "window_title": window_title,
            "region_x": region.x,
            "region_y": region.y,
            "region_width": region.width,
            "region_height": region.height,
            "dataset_path": dataset_path.as_posix(),
            "note": note,
            "processed": "no",
        })


def capture_once(
    args: argparse.Namespace,
    user32: ctypes.CDLL,
    gdi32: ctypes.CDLL,
    mode: str,
    capture_number: int,
) -> Path:
    region, window_title = resolve_target_region(user32, args)
    path = screenshot_path(args.output_dir, args.prefix)
    captured_at = dt.datetime.now()
    capture_region(path, region, user32, gdi32)
    append_index(args.index_csv, path, captured_at, mode, region, window_title, args.dataset_path, args.note)
    show_capture_indicator(region, user32, gdi32, args.indicator_ms)
    print(f"[{capture_number:03}] saved {path} ({region.label()})")
    if window_title and window_title not in ("manual-region", "virtual-desktop"):
        print(f"      window: {window_title}")
    return path


def register_hotkeys(user32: ctypes.CDLL) -> None:
    if not user32.RegisterHotKey(None, HOTKEY_CAPTURE_ID, MOD_NOREPEAT, VK_NUMPAD0):
        raise OSError("Could not register Num0 hotkey. Another app may already use it.")
    if not user32.RegisterHotKey(None, HOTKEY_EXIT_ID, MOD_NOREPEAT, VK_ESCAPE):
        user32.UnregisterHotKey(None, HOTKEY_CAPTURE_ID)
        raise OSError("Could not register Esc hotkey. Another app may already use it.")


def unregister_hotkeys(user32: ctypes.CDLL) -> None:
    user32.UnregisterHotKey(None, HOTKEY_CAPTURE_ID)
    user32.UnregisterHotKey(None, HOTKEY_EXIT_ID)


def run_hotkey_mode(args: argparse.Namespace, user32: ctypes.CDLL, gdi32: ctypes.CDLL) -> int:
    print("Capture mode ready.")
    print("Press Num0 to save a screenshot.")
    print("Press Esc or Ctrl+C to stop.")
    print(f"Output: {args.output_dir.resolve()}")
    print(f"Index:  {args.index_csv.resolve()}")

    register_hotkeys(user32)
    captures = 0
    msg = MSG()
    try:
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message != WM_HOTKEY:
                continue

            hotkey_id = int(msg.wParam)
            if hotkey_id == HOTKEY_EXIT_ID:
                break

            if hotkey_id == HOTKEY_CAPTURE_ID:
                captures += 1
                capture_once(args, user32, gdi32, "hotkey", captures)
    except KeyboardInterrupt:
        print("\nStopping capture mode.")
    finally:
        unregister_hotkeys(user32)
    return captures


def run_interval_mode(args: argparse.Namespace, user32: ctypes.CDLL, gdi32: ctypes.CDLL) -> int:
    if args.delay > 0:
        print(f"Starting in {args.delay:g}s...")
        time.sleep(args.delay)

    total = "unlimited" if args.count <= 0 else str(args.count)
    print(f"Automatic capture every {args.interval:g}s ({total} capture(s)).")
    print("Press Ctrl+C to stop.")
    print(f"Output: {args.output_dir.resolve()}")
    print(f"Index:  {args.index_csv.resolve()}")

    captures = 0
    try:
        while args.count <= 0 or captures < args.count:
            captures += 1
            capture_once(args, user32, gdi32, "interval", captures)
            if args.count > 0 and captures >= args.count:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopping automatic capture.")
    return captures


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture Tracker.gg scoreboards for tracker score calibration.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default="data/scoreboard_screens",
        help="Directory where screenshots are saved."
    )
    parser.add_argument("--prefix", default="scoreboard", help="Screenshot filename prefix.")
    parser.add_argument(
        "--index-csv",
        type=Path,
        default=Path("data/scoreboard_screens/index.csv"),
        help="CSV index that tracks captured screenshots and processing status."
    )
    parser.add_argument(
        "--dataset-path",
        type=Path,
        default=Path("data/tracker_score_samples.csv"),
        help="Calibration CSV these screenshots are intended to expand."
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.0,
        help="Capture automatically every N seconds. Use 0 for Num0 hotkey mode."
    )
    parser.add_argument("--count", type=int, default=0, help="Number of automatic captures. 0 means until Ctrl+C.")
    parser.add_argument("--delay", type=float, default=0.0, help="Seconds to wait before automatic captures start.")
    parser.add_argument(
        "--window-title",
        default="",
        help="Capture the first visible window whose title contains this text, e.g. tracker.gg."
    )
    parser.add_argument("--region", type=parse_region, help="Capture x,y,width,height instead of the full screen/window.")
    parser.add_argument("--all-screens", action="store_true", help="Capture the whole virtual desktop across every monitor.")
    parser.add_argument("--note", default="", help="Free text stored in the screenshot index CSV.")
    parser.add_argument(
        "--indicator-ms",
        type=int,
        default=250,
        help="Duration of the green capture flash in milliseconds. Use 0 to disable it."
    )
    parser.add_argument("--list-windows", action="store_true", help="Print visible window titles and exit.")
    parser.add_argument("--once", action="store_true", help="Take one screenshot immediately and exit.")
    args = parser.parse_args()

    if args.interval < 0:
        parser.error("--interval must be 0 or greater.")
    if args.delay < 0:
        parser.error("--delay must be 0 or greater.")
    if args.window_title and args.region:
        parser.error("--window-title and --region cannot be used together.")
    if args.region and args.all_screens:
        parser.error("--region and --all-screens cannot be used together.")
    if args.indicator_ms < 0:
        parser.error("--indicator-ms must be 0 or greater.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    user32, gdi32 = ensure_windows()

    if args.list_windows:
        for title, region in list_visible_windows(user32):
            print(f"{region.label()}  {title}")
        return

    if args.once:
        captures = 1
        capture_once(args, user32, gdi32, "once", captures)
    elif args.interval > 0:
        captures = run_interval_mode(args, user32, gdi32)
    else:
        captures = run_hotkey_mode(args, user32, gdi32)

    print(f"Done. Captured {captures} screenshot(s).")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
