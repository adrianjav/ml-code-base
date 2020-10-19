# MLSuite

This is a work-in-progress library that I use in order to speed up the boilerplate involved in every research machine learning code.

You can install the library using `pip install git+https://github.com/adrianjav/ml-code-base.git`

Check the code in `example.py` to see how `MLSuite` is used, and try running `python example.py --help` and `python example.py -c example-settings.yml -device cuda --exist-ok`.

Main features:

- Creates a folder per experiment and changes the working directory (transparent to the code).
- All the configuration is accessible using dot notation, `args.myoption`.
- Redirects standard output/error to text files (with `verbose` it still prints to the console if the shell is interactive)

- Enables configuration reading through YAML files.
  - Accepts more than one file, later files overwrite previous configurations (overwrite != replace).
  - The configuration files accept placeholders, that is, use other values of the configuration, through the syntax `${variable_name}`.
- Enables console arguments (you can add your own arguments using `click`)
- Saves a copy of the configuration in the experiment folder.
- Add a timestamp to the configuration file (accessible through `${options.timestamp}`)
- It does not allow you re-run an experiment if the git version is not the same as when the experiment was first run.

Other utilities:

- Functionality to properly fix the seed.
- `@keyboard_stoppable`, decorator to interrupt a function using the keyboard.
- `@timed`, decorator to time how long a function takes.

To come:

- Automatic and transparent loading/saving of models.