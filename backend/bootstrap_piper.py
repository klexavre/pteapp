import json
import os
import platform
import shutil
import stat
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
PIPER_DIR = APP_DIR / ".piper"
VOICES_DIR = APP_DIR / "voices"
PIPER_BIN = PIPER_DIR / ("piper.exe" if os.name == "nt" else "piper")
RUNTIME_STATE = PIPER_DIR / "runtime.json"
VOICE_MODEL = VOICES_DIR / "en_US-lessac-low.onnx"
VOICE_JSON = VOICE_MODEL.with_suffix(VOICE_MODEL.suffix + ".json")


def download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {destination.name}...")
    urllib.request.urlretrieve(url, destination)


def extract_archive(archive_path: Path, dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path) as zf:
            zf.extractall(dest_dir)
    elif archive_path.suffixes[-2:] == [".tar", ".gz"] or archive_path.suffix == ".tgz":
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(dest_dir)
    else:
        raise RuntimeError(f"Unsupported archive format: {archive_path}")


def ensure_piper_binary() -> Path:
    if PIPER_BIN.exists():
        return PIPER_BIN

    existing_path = shutil.which("piper")
    if existing_path:
        resolved_path = Path(existing_path)
        if resolved_path != PIPER_BIN:
            shutil.copy2(resolved_path, PIPER_BIN)
        os.chmod(PIPER_BIN, os.stat(PIPER_BIN).st_mode | stat.S_IEXEC)
        return PIPER_BIN

    PIPER_DIR.mkdir(parents=True, exist_ok=True)
    system = platform.system().lower()
    if os.name == "nt":
        archive_name = "piper_windows_amd64.zip"
        download_url = "https://github.com/rhasspy/piper/releases/latest/download/piper_windows_amd64.zip"
    elif system == "linux":
        archive_name = "piper_linux_x86_64.tar.gz"
        download_url = "https://github.com/rhasspy/piper/releases/latest/download/piper_linux_x86_64.tar.gz"
    elif system == "darwin":
        archive_name = "piper_macos_x64.tar.gz"
        download_url = "https://github.com/rhasspy/piper/releases/latest/download/piper_macos_x64.tar.gz"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")

    archive_path = PIPER_DIR / archive_name
    download_file(download_url, archive_path)
    extract_archive(archive_path, PIPER_DIR)

    for candidate in sorted(PIPER_DIR.rglob("piper*")):
        if not candidate.is_file():
            continue
        name_lower = candidate.name.lower()
        if name_lower == "piper.exe" or name_lower == "piper":
            if candidate != PIPER_BIN:
                shutil.copy2(candidate, PIPER_BIN)
            os.chmod(PIPER_BIN, os.stat(PIPER_BIN).st_mode | stat.S_IEXEC)
            return PIPER_BIN

    if not PIPER_BIN.exists():
        raise RuntimeError("Piper binary was downloaded but not found in the extracted files.")

    return PIPER_BIN


def ensure_voice_model() -> tuple[Path, Path]:
    VOICES_DIR.mkdir(parents=True, exist_ok=True)
    if VOICE_MODEL.exists() and VOICE_JSON.exists():
        return VOICE_MODEL, VOICE_JSON

    model_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/low/en_US-lessac-low.onnx"
    json_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/low/en_US-lessac-low.onnx.json"
    download_file(model_url, VOICE_MODEL)
    download_file(json_url, VOICE_JSON)
    return VOICE_MODEL, VOICE_JSON


def write_runtime_state(piper_bin: Path, voice_model: Path, voice_json: Path) -> None:
    RUNTIME_STATE.write_text(
        json.dumps(
            {
                "piper_bin": str(piper_bin),
                "voice_model": str(voice_model),
                "voice_json": str(voice_json),
            }
        ),
        encoding="utf-8",
    )


def main() -> None:
    try:
        piper_bin = ensure_piper_binary()
        voice_model, voice_json = ensure_voice_model()
        write_runtime_state(piper_bin, voice_model, voice_json)
        print(f"Piper available at: {piper_bin}")
        print(f"Voice model available at: {voice_model}")
        print(f"Voice config available at: {voice_json}")
    except Exception as exc:
        print(f"Piper bootstrap failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
