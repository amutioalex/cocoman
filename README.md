<h1 align="center">cocoman</h1>
<h4 align="center">making cocotb regressions less stressful 🚀</h4>

<p align="center">
  <a href="#description">📜 Description</a> •
  <a href="#setup">⚙️ Setup</a> •
  <a href="#usage">🛠️ Usage</a> •
  <a href="#limitations">⚠️ Limitations</a> •
  <a href="#contributing">🤝 Contributing</a> •
  <br>
  <br>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff"
         alt="Python Programming Language">
  </a>
  <a href="/LICENSE">
    <img src="https://img.shields.io/badge/License-BSD_3--Clause-blue.svg"
         alt="BSD 3-Clause">
  </a>
</p>

# 📜 Description <a id="description"></a>

**cocoman** is your trusted companion for running
**[cocotb](https://github.com/cocotb/cocotb)-based regressions** without losing your
mind.
- 🧩 Manage **ALL** your testbenches in a single YAML.
- 📂 Say goodbye to directory drama and run your testbench **from anywhere**.
- 🎯 **Choose your scope**: run everything or just the stuff you care about.
- 🔧 **Customize** build/test parameters.

# ⚙️ Setup <a id="setup"></a>

> This package works with **Python>=3.9** and **cocotb<2**.

## Option 1: Stable Version

```bash
# Install from PyPI
$ pip install cocoregman

# Or download and install the latest release
$ pip install cocoman-*.tar.gz
```

## Option 2: Living on the Edge

```bash
# Clone the repository
$ git clone https://github.com/amutioalex/cocoman.git
$ cd cocoman
# Install
$ pip install .
```

---

# 🛠️ Usage <a id="usage"></a>

**cocoman** needs a YAML file called a **runbook** to configure the regression run.

You can find a runbook example in `examples/.cocoman`.

## Runbook Options

- `general`: Defines basic regression parameters.
  - `sim`: The simulator to use.
  - `srcs`: Indexed dictionary of source file paths.
  - `build_args`/`test_args`: Global configurations for build/test parameters.

- `tbs`: Defines testbenches.
  - `tags`: List of names for testbench filtering.
  - `srcs`: References to indexed sources.
  - `path`: Directory containing the testbench.
  - `hdl`: HDL used in the top module.
  - `rtl_top`: Design top-level module.
  - `tb_top`: Testbench top module (Python).
  - `build_args`/`test_args`: Custom arguments for the
    [cocotb.runner.Simulator](https://docs.cocotb.org/en/stable/library_reference.html#python-test-runner)
    `build`/`test` methods.

- `include`: List of directories containing additional Python modules for the
  testbenches.

> Environment and user variables in source, include, and testbench paths are expanded.
> Non-absolute paths are interpreted relative to the runbook YAML file's directory.
> Strings in the `build_args` and `test_args` sections containing environment or user
> variables are expanded, but they are not interpreted as relative paths.

> The `general` section contains global options like `sim`, `build_args`, ...
> For backward compatibility, these options may also be defined at the top level of the
> runbook. However, if the `general` section is present, the top-level definitions of
> those same options will be ignored.

> Testbench-specific `build_args` and `test_args` override global settings.

## Commands

> If no path to a runbook is provided, the tool will look for a `.cocoman` file in the
> current working directory, which should contain a valid runbook in YAML format.

### `list`

```bash
$ cmn list [-t <name>] [<path>]
```
Display a general overview of the runbook configuration.
- *-t*: Indicate a testbench name to display its specific overview instead.

### `run`

```bash
$ cmn run RUNBOOK [-d] [-t <name> [<name> ...]] [-n <int>] [-i <pattern>
[<pattern> ...]] [-e <pattern> [<pattern> ...]] [-I <pattern> [<pattern> ...]]
[-E <pattern> [<pattern> ...]] [-g] [<path>]
```
Run a testbench regression.
- *-d*: Dry run mode. Display execution plan instead of running it.
- *-t*: List of testbenches, to run. If none, run all.
- *-n*: Number of times each test should be run.
- *-i*: Patterns of testcase names to run exclusively. Others are ignored.
- *-e*: Patterns of testcase names to ignore. Other testcases are run.
- *-I*: Patterns of tags to run exclusively. Others are ignored.
- *-E*: Patterns of tags tags to ignore. Other testbenches are run.
- *-g*: Whether the input patterns should be treated as `globex` or not.

> Inclusion (`-i`, `-I`) is applied before exclusion (`-e`, `-E`).

## Running An Example

A working example is available in the `examples` directory:
```bash
$ cd examples/ # Ensure correct working directory
$ export COCOMAN_EXAMPLES_DIR=`git rev-parse --show-toplevel`/examples
$ cmn list
$ cmn list -t mini_counter_tb
$ cmn run -t mini_counter_tb -n 3
...
```

# ⚠️ Limitations <a id="limitations"></a>

- **pyuvm integration**: When using [pyuvm](https://github.com/pyuvm/pyuvm), the
  `uvm_test` class must be wrapped in a cocotb test. For details, see
  [this note](https://github.com/pyuvm/pyuvm/releases/tag/2.9.0).
- **Handling test failures**: If tests fail, consider whether the issue originates from
  testbench design. For example, instantiating multiple clocks in cocotb can cause
  issues in consecutive tests.

# 🤝 Contributing <a id="contributing"></a>

The testing scope of this tool is very limited at the moment, so errors will likely
appear as users set up **cocoman** for their specific workflows.

Nonetheless, contributions are welcomed! Feel free to open a GitHub Issue for bugs or
suggestions.
