---
name: uv-package-test
description: Instructions for setting up a Python package development environment using `uv` and `pytest`.
---

This part is adapted from [this post](https://pydevtools.com/handbook/tutorial/setting-up-testing-with-pytest-and-uv/).

To set up the package development environment using `uv`, run the following commands:

```sh
uv init --package
```

`uv` will create a virtual environment and set up the basic structure for your package. Most importantly, outside `src/` directory, you can import your package as if it is installed.

```sh
uv add --dev pytest
mkdir tests
```

Now write tests in the `tests` directory and run them using:

```sh
uv test
```