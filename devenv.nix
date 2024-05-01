{
  pkgs,
  lib,
  config,
  ...
}: {
  pre-commit = {
    hooks = {
      check-merge-conflicts.enable = true;
      check-added-large-files.enable = true;
      editorconfig-checker.enable = true;
      ruff.enable = true;
      poetry-check.enable = true;
      mypy = {
        enable = true;
        settings.binPath = ''.venv/bin/mypy'';
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
    pi = {
      exec = ''
        ${pkgs.uv} pip $@
      '';
      description = "Replacing pip with uv pip";
    };
  };

  languages.python = {
    enable = true;
    uv = {
      enable = true;
      package = pkgs.uv;
    };
    poetry = {
      enable = true;
      activate.enable = true;
      install = {
        installRootPackage = true;
        enable = true;
        quiet = true;
      };
      install.allExtras = true;
    };
  };

  enterShell = ''
    echo
    echo 🦾 Useful project scripts:
    echo 🦾
    ${pkgs.gnused}/bin/sed -e 's| |••|g' -e 's|=| |' <<EOF | ${pkgs.util-linuxMinimal}/bin/column -t | ${pkgs.gnused}/bin/sed -e 's|^|🦾 |' -e 's|••| |g'
    ${lib.generators.toKeyValue {} (lib.mapAttrs (name: value: value.description) config.scripts)}
    EOF
    echo
  '';
}
