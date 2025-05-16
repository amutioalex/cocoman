<h1 align="center">cocoman</h1>
<h4 align="center">making cocotb regressions less stressful 🚀</h4>

<p align="center">
  <a href="#description">📜 Description</a> •
  <a href="#setup">⚙️ Setup</a> •
  <a href="#usage">🛠️ Usage</a> •
  <a href="#limitations">⚠️ Limitations</a> •
  <a href="#contributing">🤝 Contributing</a> •
  <a href="#alternative-access">🌐 Alternative Access </a>
  <br>
  <br>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff"
         alt="Python Programming Language">
  </a>
  <a href="/LICENSE">
    <img src="https://img.shields.io/badge/License-GPLv3-blue.svg"
         alt="GNU GPLv3">
  </a>
</p>

# 📜 Description <a id="description"></a>

**cocoman** is your trusted companion for running **[cocotb](https://github.com/cocotb/cocotb)-based regressions**
without losing your mind.
- 🧩 Manage **ALL** your testbenches in a single YAML.
- 📂 Say goodbye to directory drama - you can run your testbench **from anywhere**.
- 🎯 **Choose your scope**: run everything or just the stuff you care about.
- 🔧 **Customize** build/test parameters like a pro.

# ⚙️ Setup <a id="setup"></a>
## Option 1: Stable Version

```bash
# Install from PyPi
$ pip install cocoregman

# Or download and install the latest release
$ python -m pip install cocoregman-*.tar.gz
```

## Option 2: Living on the Edge

```bash
# Clone the repository
$ git clone https://github.com/amutioalex/cocoman.git
$ cd cocoman
# Install in editable mode
$ python -m pip install -e .
```

> The `main` branch contains stable features, whereas `dev` is meant for features that
> might still need some testing.

---

# 🛠️ Usage <a id="usage"></a>

**cocoman** needs a YAML file called a **runbook** to do its thing. Think of it as your
regression playlist.

You can find a runbook example in `examples/.cocoman`.

## Runbook Options

- `sim`: The simulator to use.
- `srcs`: Indexed dictionary of source file paths.
- `tbs`: Defines testbenches.
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
- `build_args`/`test_args`: Global configurations for build/test parameters.

> Environment and user variables in source, include, and testbench paths are expanded.
> Non-absolute paths are interpreted relative to the runbook YAML file's directory.
> Strings in the `build_args` and `test_args` sections containing environment or user
> variables are expanded, but they are not interpreted as relative paths.

> Testbench-specific `build_args` and `test_args` override global settings.

## Commands

> If no path to a runbook is provided, the tool will look for a `.cocoman` file in the
> current working directory, which should contain a valid runbook in YAML format.

### `list`

```bash
$ cmn list [-t TBNAME] [RUNBOOK]
```
Display a general overview of the runbook setup in a formatted way.
- *-t*: Indicate a testbench name to display its overview instead.

### `run`

```bash
$ cmn run RUNBOOK [-d] [-t TBNAME [TBNAME]] [-n NTIMES] [-i TSTNAME [TSTNAME]]
[-e TSTNAME [TSTNAME]] [-I TAGNAME [TAGNAME]] [-E TAGNAME [TAGNAME]] [RUNBOOK]
```
Run a testbench regression.
- *-d*: Dry run mode. Display execution plan instead of running it.
- *-t*: List of testbenches, to run. If none, run all.
- *-n*: Number of times each test should be run.
- *-i*: List of testcases to run exclusively. Others are ignored.
- *-e*: List of testcases to ignore. Other testcases are run.
- *-I*: List of testbench tags to run exclusively. Others are ignored.
- *-E*: List of testbench tags to ignore. Other testbenches are run.

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
  testbench design. For example, instantiating multiple clocks in cocotb can cause issues
  in consecutive tests.

# 🤝 Contributing <a id="contributing"></a>

The testing scope of this tool is very limited at the moment, so errors will likely
appear as users set up **cocoman** for their specific workflows.

Nonetheless, contributions are welcomed! Feel free to open an Issue for bugs or
suggestions.

# 🌐 Alternative Access <a id="alternative-access"></a>

Official releases are also mirrored on
[Codeberg](https://codeberg.org/amutioalex/cocoman/releases) for those who prefer a
non-GitHub platform.

> Source code and development happen here on [GitHub](https://github.com/amutioalex/cocoman), 
> but release artifacts (`.tar.gz`, etc.) are published to both platforms.
