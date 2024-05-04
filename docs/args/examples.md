# Examples

WARNING: This section is a work in progres and in some places it is outdated.

Lets first look at a trivial example and explain it along and then provide more complex scenarios

## Trivial Example

Consider the following folder structure

```
.
├── main.py
└── temp.yaml
```

where `temp.yaml` has the following contents

```yaml
is_atro_args_example: true
```

while `main.py` has the following contents

```python
from atro_core.args import Arg, InputArgs

input_args = InputArgs()

# Specify source
input_args.include_source("./temp.yaml")

# Add arguments
input_args.add_arg(
    Arg(
        name="is_atro_args_example",
        arg_type=bool,
        help="Just an example",
        required=True,
    )
)

# Create model
model = input_args.get_dict()
```

`model` in the example above would be `model = {'is_atro_args_example': True}`.

As mentioned above first the InputArgs is instantiated, we then include a source which happens to be the `temp.yaml` file, this can be passed as a string or a `Path` type, here I opted for string. I then instruct what argument I want to add, specifying some help, the type I want it to be and insist that it is present, if its missing an ValueError will be raised.

!!! warning "Types"
Below one can see the use of `arg_type=int` and `arg_type=str`, other types like `bool` and `float` are also supported. In principle even more complex types such as `dict` and `list` are supported, but they are rarely good use-case with this package, it is _usually_ better to use `yaml` or `json` files for those and load using `pyyaml` or `json` instead of this package.

## Environment variables

For sake of the example suppose you have (somehow) passed in the environment variables `ATRO_TEST_APP_NAME` and `ATRO_TEST_RANDOM_NUMBER` with values `test` and `10` respectively.

The prefix here is `ATRO_TEST`. The remaining part of the environment variable must match the "name" argument in the Arg part.

```python
# Setup
from atro_core.args import Arg, InputArgs

input_args = InputArgs(prefix="ATRO_TEST")
input_args.add_arg(Arg(name="random_number", arg_type=int, help="Just some random number", required=True))
input_args.add_arg(Arg(name="app_name", arg_type=str, help="App name", required=True))

# Obtain the model (of type dict[str, Any])
model = input_args.get_dict()

# Show that indeed we have the correct values
assert type(model.get("app_name")) == str
assert type(model.get("random_number")) == int

assert model.get("app_name") == "test"
assert model.get("random_number") == 10
```

## Command line arguments

Suppose you have a file called `some_file.py` with the following contents:

```python
from atro_core.args import Arg, InputArgs

# Setup
input_args = InputArgs()
input_args.add_arg(Arg(name="random-number", arg_type=int, help="Just some random number", required=True))

# Show that indeed we have the correct values
model = input_args.get_dict()

print(model.get("random-number"))
if model.get("random-number"):
  assert type(model.get("random-number")) == int
```

If one runs the following command:

```bash
python some_file.py --random-number 10
```

you'd see that the output is `10` and the assertion passes.

If one runs the following command:2

```bash
python some_file.py --random-number 10.0
```

you'd see a `ValueError` being raised as the type is incorrect.

## Environment files

For this example suposse we have a file called `.env` in the same directory where the python file is with the following contents:

```bash
ATRO_TEST_APP_ENV_FILE_NAME="test"
ATRO_TEST_RANDOM_ENV_FILE_NUMBER=10
```

then the following code would work:

```python
# Setup
env_files: list[Path] = [Path(__file__).parent / ".env"]
input_args = InputArgs(prefix="ATRO_TEST", env_files=env_files)
input_args.add_arg(Arg(name="app_env_file_name", arg_type=str, help="App name", required=False))

# Create model
model = input_args.get_dict()

assert model.get("app_env_file_name") == "test"
```

requesting random_env_file_number would also work, but it is not shown here for brevity.

## YAML files

Consider the following yaml file (called `test.yaml`) which is in the same directory as the python file:

```yaml
app_yaml_file_name: "test"
random_yaml_file_number: 10
```

then the following code would work:

```python
# Setup
yaml_files = [Path(__file__).parent / "test.yaml"] if provided else []
input_args = InputArgs(prefix="ATRO_TEST", yaml_files=yaml_files)
input_args.add_arg(Arg(name="app_yaml_file_name", arg_type=str, help="App name", required=False))

# Create model
model = input_args.get_dict()

# Assert
assert model.get("app_yaml_file_name") == "test"
```

## Populate class instance

We easily can populate a pydantic BaseModel

### Populate AppSettings

To populate pydantic BaseClass with loaded parameters

```python
class Settings(BaseModel):
    NAME: str
    HOST: str
    PORT: int
    OPTIONAL_PARAMETER: str = "DEFAULT"
    NULLABLE_PARAMETER: Optional[str]

app_settings = InputArgs(prefix="MYPREFIX").populate_cls(Settings, cli_args)
```

!!! info "Work in progress"
In the future the intention is to use `pyyaml` and `json` to load data from yamls and jsons on users behalf along with all the other sources of input. Currently json is not supported and yaml is in its early stages of support.
