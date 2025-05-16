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
# Download and install the latest release
$ python -m pip install cocoman-*.tar.gz
```

## Option 2: Living on the Edge

```bash
# Clone the repository
$ git clone https://github.com/amutioalex/cocoman.git
$ cd cocoman
# Install in editable mode
$ python -m pip install -e .
```

# 🛠️ Usage <a id="usage"></a>

**cocoman** needs a YAML file called a **runbook** to do its thing. Think of it as your
regression playlist.

## Example Runbook (`examples/.cocoman`)

```yaml
sim: icarus
srcs:
  1: ${COCOMAN_EXAMPLES_DIR}/mini_counter/mini_counter.sv
  2: ./big_counter/big_counter.sv
tbs:
  mini_counter_tb:
    srcs: [1]
    path: ./mini_counter
    hdl: verilog
    rtl_top: mini_counter
    tb_top: mini_tb
  big_counter_tb:
    srcs: [1, 2]
    path: ./big_counter
    hdl: verilog
    rtl_top: big_counter
    tb_top: big_tb
    build_args:
      waves: False
    test_args:
      waves: False
include:
  - ${COCOMAN_EXAMPLES_DIR}
build_args:
  build_dir: ./simdir
  waves: True
test_args:
  test_dir: ./simdir
  waves: True
```
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

> Environment variables in paths are resolved. Non-absolute paths are interpreted
> relative to the runbook YAML file's directory — **except** for paths in the
> `build_args` and `test_args` sections, which are interpreted relative to the current
> working directory.

> Testbench-specific `build_args` and `test_args` override global settings.

## Commands

> If no path to a runbook is provided, the tool will look for a `.cocoman` file in the
> current directory, which should contain a valid runbook in YAML format.

### `list`

```bash
$ cmn list [RUNBOOK]              # Show runbook info
$ cmn list [RUNBOOK] [-t TBNAME]  # Show testbench-specific info
```

### `run`

```bash
$ cmn run [RUNBOOK]                     # Run all tests
$ cmn run [RUNBOOK] [-t [TBNAME ...]]   # Run tests for a specific testbench
$ cmn run [RUNBOOK] [-n NTIMES]         # Repeat tests N times
$ cmn run [RUNBOOK] [-i [TSTNAME ...]]  # Run only selected tests
$ cmn run [RUNBOOK] [-e [TSTNAME ...]]  # Exclude selected tests
```
> Inclusion (`-i`) is applied before exclusion (`-e`).

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
