## General instructions: Develop new package with `uv`

This part is adapted from [this post](https://pydevtools.com/handbook/tutorial/setting-up-testing-with-pytest-and-uv/).

To set up the package development environment using `uv`, run the following commands:

```sh
uv init --package
uv add --dev pytest
mkdir tests
```

Now write tests in the `tests` directory and run them using:

```sh
uv test
```

## Code style

### Pydantic

- Prefer `Annotated` style.
- We are in Python 3.13, use newest syntax.