# Usage

At its core, usage of atro-args should be very simple, you instantiate a class, instruct it where to get the configs from and what configs to get, thats it.

## Including sources

In order to get the data, we need to know sources to get this data from. By default atro-args looks at cli-arguments, `.env` file and environment variables with given prefix, if no prefix is provided at instantiation of InputArgs a default prefix of `ATRO_ARGS` is used.

Sources are a list of either strings or of type Path (from pathlib). If a path is provided it is expected to point to a file that contains the needed data, currently `ini, yaml, json, toml, env` are the only supported file formats, any other format will raise an exception.

If a string is provided it is first checked if it happens to be one of 2 special strings, `cli` or `envs`, `cli` refers to cli arguments, while `envs` refers to environment variables. If its neither `cli` or `envs` an attempt is made to interpret it as a path to a file as above, if this fails an exception is raised.

Do note the order of elements in sources matters, first on the list is prioritied over the rest, if the same variable appears in two places it is not overwritten. Because of this you may want to replace the defaults entirely, this can be done with the `set_source` and `set_sources` functions. If instead you simply want to add more sources this can be done with `include_source` and `include_sources` or simply `include`.

In total there are 3 ways to include args,

- Via sources parameter during `InputArgs` instance initialisation
- Via `include_source` passing either a string or a path, a stiring can be either a path representation, "cli" or "envs".
- Via `include_sources` passing a list of elements. Each element is either a string or a path, a stiring can be either a path representation, "cli" or "envs".

## Adding arguments

Adding arguments should tell the package what arguments you expect to obtain from the sources provided. Note you do not have to provide sources first and then arguments, as long as they are both provided before reconciliations (via say `get_dict()` function). Arguments can be added via `add_arg`, `add_args` or `add`, note `add` is just an alias to `add_arg`. You can also create a dataclass or a pydantic class and add that class, this will add all of that classes public properties as arguments.

In total there are 5 ways of providing arguments

- Via args parameter during `InputArgs` instance initialisation
- Via `include_arg` on `InputArgs` instance, passing a single `Arg` element.
- Via `include_args` on `InputArgs` instance, passing a list of `Arg` elements
- Via `add` on `InputsArgs` instance, passing params that would be typically passed into Arg (this is purely for convenience).
- Via `add_cls` on `InputArgs` instance, passing a class that is either a dataclass or pydantic class, public properties are then added as arguments.

## Getting the config

Assuming we now have an instance of `InputArgs` with correct arguments added and sources included we can now get the data back in multiple ways, depending what is convinient.

We can call `get_dict()` to get a dictionary with keys being the names of arguments provided, while the values will be the sourced configuration values form the sources provided.

We can also do `get_cls(...)` which takes the class type as an input and outputs an instance of that class with its parameters populated. Note this is only supported for data classes and pydantic classes.

By far shortes way of using this package is to use `populate_cls()` where a class type is provided and populated on the spot. All one has to do is instantiate `InputArgs` with correct prefix and sources, and call `populate_cls()` on it and that is it, this is of course not as flexible as the methods above so it may not be good for every use-case.

In addition to the above we can also decorate a function to take inputs from the config, look at examples section for examples how this is done.
