# sawmill-plugin-vivado

A Sawmill plugin for parsing Xilinx Vivado synthesis, implementation, and bitstream logs.

See [Sawmill](https://github.com/sjalloq/sawmill) for more info.

## Installation

```bash
[uv] pip install git+https://github.com/sjalloq/sawmill-plugin-vivado.git
```

Or for development:

```bash
git clone https://github.com/sjalloq/sawmill-plugin-vivado.git
cd sawmill-plugin-vivado
make install
```

Confirm it's registered:

```bash
sawmill --list-plugins
```

## Usage

```bash
# Launch the TUI on a Vivado log
sawmill vivado.log

# Filter to errors and critical warnings only
sawmill vivado.log --severity error
sawmill vivado.log --severity critical_warning

# CI mode — fail on warnings and above
sawmill vivado.log --check

# Fail only on errors
sawmill vivado.log --check --fail-on error
```

## What It Parses

Vivado logs use this message format:

```
TYPE: [Category ID-Number] message text [/path/to/file.v:line]
```

For example:

```
INFO: [Synth 8-6157] synthesizing module 'top' [/src/top.v:53]
WARNING: [Vivado 12-3523] Attempt to change 'name' is not allowed
CRITICAL WARNING: [Constraints 18-4427] Constraint override warning
ERROR: [Route 35-9] Routing failed
```

The plugin handles multi-line messages (indented continuation lines, tables)
and extracts file references from both `[/path:line]` and `/path:line` formats.

## Severity Levels

| ID | Name | Level | Style |
|----|------|-------|-------|
| `error` | Error | 3 | red bold |
| `critical_warning` | Critical Warning | 2 | red |
| `warning` | Warning | 1 | yellow |
| `info` | Info | 0 | cyan |

## Detection

The plugin identifies Vivado logs by checking (in order of confidence):

1. **Vivado header** (`# Vivado v2025.2 ...`) — 0.95
2. **Multiple Vivado message IDs** (Synth, DRC, Timing, etc.) — 0.85
3. **Severity pattern density** (5+ matching lines) — 0.6
4. **Filename contains "vivado"** — 0.4

## Domain-Specific Filters

These filters let you focus on specific Vivado subsystems. Severity filtering
(errors, warnings, etc.) is handled by sawmill's built-in `--severity` flag and
TUI severity toggles.

| Filter | Pattern | Description |
|--------|---------|-------------|
| Timing Issues | `(timing\|slack\|WNS\|TNS\|setup\|hold)` | Timing-related messages |
| Synthesis | `\[Synth \d+-\d+\]` | Synthesis messages |
| DRC | `\[DRC \d+-\d+\]` | Design Rule Check messages |
| Constraints | `\[Constraints \d+-\d+\]` | Constraint-related messages |
| IP Flow | `\[IP_Flow \d+-\d+\]` | IP core generation messages |
| Routing | `\[Route \d+-\d+\]` | Routing messages |

## How It Works

Sawmill discovers plugins via Python entry points. This plugin declares its
entry point in `pyproject.toml`:

```toml
[project.entry-points."sawmill.plugins"]
vivado = "sawmill_plugin_vivado:VivadoPlugin"
```

Running `pip install -e .` registers it. Sawmill calls `can_handle()` on each
plugin to auto-detect which one should parse a given log file.

## Testing

```bash
make test    # 46 tests
make lint    # ruff check + format
```

## Notes

* Does the wider Xilinx toolset use the same log style?  Would this work for Vitis et al?
