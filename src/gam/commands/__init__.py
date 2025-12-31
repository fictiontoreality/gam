"""Command handlers for gam CLI."""

from .autostart import cmd_autostart
from .category import cmd_category
from .down import cmd_down
from .logs import cmd_logs
from .ls import cmd_ls
from .restart import cmd_restart
from .search import cmd_search
from .show import cmd_show
from .status import cmd_status
from .tag import cmd_tag
from .up import cmd_up
from .validate import cmd_validate

__all__ = [
    'cmd_autostart',
    'cmd_category',
    'cmd_down',
    'cmd_logs',
    'cmd_ls',
    'cmd_restart',
    'cmd_search',
    'cmd_show',
    'cmd_status',
    'cmd_tag',
    'cmd_up',
    'cmd_validate',
]
