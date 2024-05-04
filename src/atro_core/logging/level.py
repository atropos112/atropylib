import logging


def str_to_level(level: str | int) -> int:
    if isinstance(level, int):
        return level
    if level.upper() in logging._nameToLevel:
        return logging._nameToLevel[level.upper()]
    raise ValueError(f"Unknown logger level: {level}")


def level_to_str(level: str | int) -> str:
    if isinstance(level, str) and level.isnumeric():
        level = int(level)
    elif isinstance(level, str):
        return level
    if level in logging._levelToName:
        return logging._levelToName[level]

    raise ValueError(f"Unknown logger level: {level}")
