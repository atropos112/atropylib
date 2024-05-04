from rich.logging import RichHandler


def rich_handler(level: int):
    return RichHandler(rich_tracebacks=True, level=level, highlighter=None, markup=True)
