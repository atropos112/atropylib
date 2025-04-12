{
  pkgs,
  lib,
  config,
  ...
}: let
  helpScript = ''
    echo
    echo 🦾 Useful project scripts:
    echo 🦾
    ${pkgs.gnused}/bin/sed -e 's| |••|g' -e 's|=| |' <<EOF | ${pkgs.util-linuxMinimal}/bin/column -t | ${pkgs.gnused}/bin/sed -e 's|^|🦾 |' -e 's|••| |g'
    ${lib.generators.toKeyValue {} (lib.mapAttrs (_: value: value.description) config.scripts)}
    EOF
    echo

  '';
in {
  env = {
    ATRO_NATS_URL = "nats://nats:4222";
    ATRO_SERVICE_NAME = "testing";
  };

  pre-commit = {
    hooks = {
      check-merge-conflicts.enable = true;
      check-added-large-files.enable = true;
      editorconfig-checker.enable = true;

      ruff = {
        enable = true;
        entry = "ruff check --fix";
      };
      mypy = {
        enable = true;
        entry = "mypy";
        excludes = ["tests/.*"];
      };
    };
  };

  enterTest = ''
    pytest --cov=./ --cov-report=xml --cache-clear --new-first --failed-first --verbose
  '';

  scripts = {
    run-docs = {
      exec = ''
        mkdocs serve
      '';
      description = "Run the documentation server";
    };
  };

  languages.python = {
    enable = true;
    version = "3.11"; # Have to use that so the libraries work
    libraries = with pkgs; [
      zlib
      libgcc # Pandas, numpy etc.
      stdenv.cc.cc
    ];
    uv = {
      enable = true;
      package = pkgs.uv;
      sync = {
        enable = true;
        allExtras = true;
      };
    };
    venv = {
      enable = true;
    };
  };

  enterShell = ''
    uv sync --quiet
    ${helpScript}
  '';
}
