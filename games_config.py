import os
from typing import Dict, List

DEFAULT_ROM_DIR = os.environ.get("GAME_ROM_DIR", "/home/pi/roms")
DEFAULT_CORE_DIR = os.environ.get("RETROARCH_CORE_DIR", "/usr/lib/libretro")

GAMES: Dict[str, Dict[str, List[str] | str]] = {
    "Doom (PrBoom)": {
        "core": "prboom_libretro.so",
        "rom": "doom.wad",
        "args": [],
    },
    "Tetris (NES)": {
        "core": "fceumm_libretro.so",
        "rom": "tetris.nes",
        "args": [],
    },
}


def _resolve_path(candidate: str, base_dir: str) -> str:
    if os.path.isabs(candidate):
        return candidate
    return os.path.join(base_dir, candidate)


def get_game_command(game_name: str) -> List[str]:
    if game_name not in GAMES:
        raise KeyError(f"Unknown game '{game_name}'")

    entry = GAMES[game_name]
    rom_path = _resolve_path(entry["rom"], DEFAULT_ROM_DIR)
    core_path = _resolve_path(entry["core"], DEFAULT_CORE_DIR)
    args: List[str] = entry.get("args", [])

    return ["retroarch", "-L", core_path, rom_path] + args
