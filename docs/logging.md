# Logging in Puma

Puma uses Python’s standard `logging` library.

## Default Behavior

- **As a CLI or main module:** Puma configures default logging so INFO and higher messages are visible.
- **In Jupyter notebooks:** Puma enables default logging so logs are visible in notebook cells.
- **As a module in another project:** Puma does not configure logging; messages are only shown if your application configures logging.

## Ground Truth Logging

Puma contains a separate 'Ground Truth' logger (GTL), which logs all actions and navigation steps that are performed on a
device during a Puma run. These logs are stored in separate log files with the `_gtl` suffix. The log lines produced by
this logger are also present in the regular log files, but the GTL logs only contain information about actions on a device.

## How to See Puma’s Logs

To see Puma logs in your own script, opt-in to Puma's default log format and level by calling:

```python
from puma.utils import configure_default_logging
configure_default_logging()
```

This is also shown in the examples above.
If you want to use your own logging format, you can configure Python logging (e.g., with `logging.basicConfig(level=logging.INFO)`).
