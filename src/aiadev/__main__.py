"""Allow ``python -m aiadev`` in addition to the installed ``aiadev`` script."""
from .cli import main

if __name__ == "__main__":  # pragma: no cover
    main()
