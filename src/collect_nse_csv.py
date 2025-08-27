from pathlib import Path
from datetime import datetime
import shutil, os, time, argparse, platform, string, ctypes

# ---------------------------------------------
# CONFIGURATION CONSTANTS
# ---------------------------------------------
# File patterns expected from NSE or the project's own scripts
DEFAULT_PATTERNS = ["MW-SGB*.csv", "nse_sgb_data*.csv"]

# Temporary/partial download suffixes to ignore
IGNORE_SUFFIXES = {".crdownload", ".part", ".tmp"}

# Directory names to skip when scanning whole drives (system/cache dirs)
SKIP_DIR_NAMES = {
    "windows", "program files", "program files (x86)", "programdata",
    "$recycle.bin", "system volume information",
    "appdata", "cache", ".cache", "temp", "tmp",
    ".git", ".svn", "node_modules", "__pycache__",
}

# ---------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------

def _guess_repo_root(script_dir: Path) -> Path:
    """
    Walk upwards from the script directory to find the repo root.
    Repo root is assumed to contain either a '.git' folder or a 'data' folder.
    """
    for p in [script_dir] + list(script_dir.parents):
        if (p / ".git").exists() or (p / "data").exists():
            return p
    return script_dir

def _list_matches(d: Path, patterns: list[str]) -> list[Path]:
    """
    List files in directory `d` that match any of the glob `patterns`,
    case-insensitive.
    """
    out = []
    try:
        for pat in patterns:
            out += list(d.glob(pat))
            out += list(d.glob(pat.lower()))
            out += list(d.glob(pat.upper()))
    except Exception:
        pass
    return out

def _is_accessible_dir(p: Path) -> bool:
    """
    Return True if directory `p` can be listed without errors
    (i.e. not encrypted, not unavailable).
    """
    try:
        with os.scandir(p):
            return True
    except Exception:
        return False

def _enumerate_accessible_roots() -> list[Path]:
    """
    Return accessible root paths to search in deep mode.

    - On Windows: use WinAPI to list logical drives and drive types,
      skip drives that are not ready or inaccessible.
    - On Linux/Mac: check root (/) and common mount points.
    """
    roots = []
    system = platform.system()

    if system == "Windows":
        # WinAPI constants for drive types
        DRIVE_UNKNOWN = 0
        DRIVE_NO_ROOT_DIR = 1
        DRIVE_REMOVABLE = 2
        DRIVE_FIXED = 3
        DRIVE_REMOTE = 4
        DRIVE_CDROM = 5
        DRIVE_RAMDISK = 6

        kernel32 = ctypes.windll.kernel32
        bitmask = kernel32.GetLogicalDrives()

        for i, letter in enumerate(string.ascii_uppercase):
            if not (bitmask >> i) & 1:
                continue
            root = Path(f"{letter}:\\")
            try:
                dtype = kernel32.GetDriveTypeW(ctypes.c_wchar_p(str(root)))
            except Exception:
                continue
            if dtype in (DRIVE_NO_ROOT_DIR, DRIVE_UNKNOWN):
                continue
            if _is_accessible_dir(root):
                roots.append(root)

    else:
        # Typical mount points on Linux/Mac
        candidates = [Path("/"), Path("/mnt"), Path("/media"), Path("/Volumes")]
        seen = set()
        for base in candidates:
            if _is_accessible_dir(base):
                roots.append(base)
                try:
                    for child in base.iterdir():
                        if child.is_dir() and _is_accessible_dir(child):
                            rp = child.resolve()
                            if rp not in seen:
                                seen.add(rp)
                                roots.append(rp)
                except Exception:
                    pass

    # Deduplicate while preserving order
    seen = set()
    uniq = []
    for r in roots:
        try:
            rp = r.resolve()
        except Exception:
            continue
        if rp not in seen:
            seen.add(rp)
            uniq.append(rp)
    return uniq

def _recent_files(dirs: list[Path], patterns: list[str], recent_minutes: int, deep: bool) -> list[Path]:
    """
    Return a list of recent CSV files (matching patterns) found
    either in given directories (`dirs`) or across all accessible roots (deep).
    """
    cutoff = time.time() - recent_minutes * 60
    files = []

    if deep:
        roots = _enumerate_accessible_roots()
        for root in roots:
            # Walk filesystem safely; prune noisy/system directories
            for current_dir, dirnames, filenames in os.walk(root, topdown=True, onerror=lambda e: None):
                # Skip noisy dirs
                dirnames[:] = [name for name in dirnames if name.lower() not in SKIP_DIR_NAMES]

                for name in filenames:
                    try:
                        p = Path(current_dir) / name

                        # Quick filters
                        if p.suffix.lower() != ".csv":
                            continue
                        if any(str(p).lower().endswith(suf) for suf in IGNORE_SUFFIXES):
                            continue

                        # Match filename against patterns (case-insensitive)
                        name_path = Path(name)
                        matched = any(
                            name_path.match(pat) or
                            name_path.match(pat.lower()) or
                            name_path.match(pat.upper())
                            for pat in patterns
                        )
                        if not matched:
                            continue

                        # Only accept recent files
                        if p.stat().st_mtime >= cutoff:
                            files.append(p)
                    except Exception:
                        continue
    else:
        # Shallow search in provided dirs
        for d in dirs:
            for p in _list_matches(d, patterns):
                try:
                    if p.is_file() and p.suffix.lower() == ".csv" and p.stat().st_mtime >= cutoff:
                        if not any(str(p).lower().endswith(suf) for suf in IGNORE_SUFFIXES):
                            files.append(p)
                except Exception:
                    continue

    # Sort by modification time (newest first)
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files

# ---------------------------------------------
# MAIN FUNCTION
# ---------------------------------------------

def collect_csv(
    patterns=None,
    keep_timestamped=True,
    fixed_name="nse_sgb_data.csv",
    recent_minutes=180,
    deep=False
) -> Path:
    """
    Find the most recent NSE CSV file and move it into <repo>/data.

    - patterns: filename patterns to search for
    - keep_timestamped: True = keep unique filename with timestamp
                        False = overwrite fixed_name each run
    - recent_minutes: only consider files modified in this time window
    - deep: if True, search entire accessible drives (slower)
    """
    patterns = patterns or DEFAULT_PATTERNS
    script_dir = Path(__file__).resolve().parent
    repo_root  = _guess_repo_root(script_dir)
    data_dir   = repo_root / "data" / "nse_sgb_data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Shallow search (common dirs)
    search_dirs = [
        Path.cwd(),
        script_dir,
        script_dir.parent,
        Path.home() / "Downloads",
    ]
    for env in ("TMP", "TEMP"):
        if os.environ.get(env):
            p = Path(os.environ[env])
            if p.is_dir():
                search_dirs.append(p)

    # Collect candidates
    candidates = _recent_files(search_dirs, patterns, recent_minutes, deep=False)
    if not candidates and deep:
        # Fall back to deep search across all drives
        candidates = _recent_files([], patterns, recent_minutes, deep=True)

    if not candidates:
        raise FileNotFoundError(
            "Could not find any recent CSVs matching: "
            + ", ".join(patterns)
            + ( "\n(searched all accessible drives)" if deep else "\n(try --deep to search all accessible drives)" )
        )

    # Pick newest file
    src = candidates[0]

    # Destination path inside <repo>/data
    dst = (
        data_dir / f"nse_sgb_data_{datetime.now():%Y%m%d_%H%M%S}.csv"
        if keep_timestamped else
        data_dir / fixed_name
    )

    # Move (fall back to copy+delete if move fails)
    try:
        shutil.move(str(src), str(dst))
    except Exception:
        shutil.copy2(str(src), str(dst))
        try:
            src.unlink()
        except Exception:
            pass

    print("Source :", src.resolve())
    print("Repo   :", repo_root.resolve())
    print("Data   :", data_dir.resolve())
    print("Moved  →", dst.resolve())
    return dst

# ---------------------------------------------
# COMMAND-LINE INTERFACE
# ---------------------------------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Collect NSE SGB CSV into <repo>/data")
    ap.add_argument("--no-timestamp", action="store_true", help="Overwrite fixed name instead of timestamp")
    ap.add_argument("--fixed-name", default="nse_sgb_data.csv", help="Filename when --no-timestamp is used")
    ap.add_argument("--minutes", type=int, default=180, help="How recent the file must be (minutes)")
    ap.add_argument("--pattern", action="append", help="Additional glob patterns (e.g., --pattern MW-SGB*.csv)")
    ap.add_argument("--deep", action="store_true", help="Search all accessible drives/mounts (slower)")
    args = ap.parse_args()

    pats = DEFAULT_PATTERNS.copy()
    if args.pattern:
        pats = args.pattern + pats

    collect_csv(
        patterns=pats,
        keep_timestamped=not args.no_timestamp,
        fixed_name=args.fixed_name,
        recent_minutes=args.minutes,
        deep=args.deep
    )
