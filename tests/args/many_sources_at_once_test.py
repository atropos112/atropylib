from os import environ
from pathlib import Path

from pytest_mock import MockerFixture

from atro_core.args import Arg, InputArgs
from atro_core.args.arg_source import ArgSource
from test_helpers import ENV_FILE, YAML_FILE


def test_all_inputs_at_once(mocker: MockerFixture) -> None:
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST", sources=[ArgSource.cli, ArgSource.envs, YAML_FILE, ENV_FILE])
    input_args.add_arg(Arg(name="app_name", arg_type=str, help="App name", required=True))
    input_args.add_arg(Arg(name="app_env_name", arg_type=str, help="App name", required=True))
    input_args.add_arg(Arg(name="app_env_file_name", arg_type=str, help="App name", required=True))
    input_args.add_arg(Arg(name="app_yaml_file_name", arg_type=str, help="App name", required=True))

    # Mock cli and env inputs
    cli_input_args = ["--app_name", "test_cli"]
    mocker.patch.dict(environ, {"ATRO_TEST_APP_ENV_NAME": "test_env"})

    # Create model
    model = input_args.get_dict(cli_input_args=cli_input_args)

    # Assert
    assert model.get("app_name") == "test_cli"
    assert model.get("app_env_name") == "test_env"
    assert model.get("app_env_file_name") == "test"
    assert model.get("app_yaml_file_name") == "test"


def test_priority(mocker: MockerFixture) -> None:
    # Setup
    input_args = InputArgs(
        prefix="ATRO_TEST",
        sources=[
            ArgSource.cli,
            YAML_FILE,
            ArgSource.envs,
            ENV_FILE,
        ],
    )
    input_args.add_arg(Arg(name="app_name", arg_type=str, help="App name", required=True))

    # Mock cli and env inputs
    cli_input_args = ["--app_name", "test_cli"]
    mocker.patch.dict(environ, {"ATRO_TEST_APP_NAME": "test_env"})

    # Create model
    model = input_args.get_dict(cli_input_args=cli_input_args)

    # Assert default priority is used (cli first)
    assert model.get("app_name") == "test_cli"

    # Change priority
    sources: list[ArgSource | Path] = [ArgSource.envs, ArgSource.cli, YAML_FILE, ENV_FILE]
    input_args.sources = sources

    # Create new model with new priority
    model = input_args.get_dict(cli_input_args=cli_input_args)

    # Assert priority change affected the result
    assert model.get("app_name") == "test_env"
