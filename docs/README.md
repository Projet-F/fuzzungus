# Documentation how-to

## Use it

1. Create a pip project in the root directory of the Fuzzungus project : 
    ```bash
    pip install -e .
    ```
2. run the following command to generate the documentation:
    ```bash
    make html #Web documentation
    make latexpdf #PDF documentation
    ```
3. The documentation will be generated in the `docs/_build/html` directory.
    - Open the `html/index.html` file in a browser to view the documentation.
    - Open the `latex/fuzzungus.pdf` file in a PDF reader to view the documentation.

## Common errors

Some characters in the docstring can cause issues, like : 
- `\n` or `\r`, if not escaped
- `~` that can be interpreted as a list item
- ...

Take your time to read the error message, it is often explicit enough to understand what is wrong.