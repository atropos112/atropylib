{
  pkgs,
  lib,
  config,
  inputs,
  ...
}: let
  pkgu = import inputs.nixpkgs-unstable {system = pkgs.stdenv.system;};

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
  packages = with pkgu; [
    python311
  ];
  env = {
    NIX_LD_LIBRARY_PATH = lib.makeLibraryPath (with pkgu; [
      python311
      zlib
      stdenv.cc.cc
    ]);
    NIX_LD = builtins.readFile "${pkgu.stdenv.cc}/nix-support/dynamic-linker";
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
        package = pkgu.basedmypy;
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
    package = pkgu.python311;
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
