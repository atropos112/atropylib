{
  pkgs,
  config,
  inputs,
  ...
}: let
  inherit (inputs.atrolib.lib) listScripts writeShellScript;
  inherit (inputs.atrolib.lib.devenv.scripts) help runDocs buildDocs;
in {
  env = {
    ATRO_NATS_URL = "nats://nats:4222";
    ATRO_SERVICE_NAME = "atropylib";
  };

  pre-commit = {
    hooks = {
      inherit (inputs.atrolib.lib.devenv.git-hooks.hooks) gitleaks markdownlint;
      check-merge-conflicts.enable = true;
      check-added-large-files.enable = true;
      editorconfig-checker.enable = true;

      ruff = {
        enable = true;
        entry = writeShellScript "ruff-check" "ruff check --fix";
      };
      mypy = {
        enable = true;
        entry = "mypy";
        excludes = ["tests/.*"];
      };
    };
  };

  enterTest = writeShellScript "test" ''
    pytest --cov=./ --cov-report=xml --cache-clear --new-first --failed-first --verbose
  '';

  scripts = {
    help = help config.scripts;
    run-docs = runDocs "docs";
    build-docs = buildDocs "docs";
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

  enterShell = listScripts config.scripts;
}
