{
  description = "My core python library to be used in all my projects";
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    pre-commit-hooks.url = "github:cachix/git-hooks.nix";
  };
  outputs = {
    self,
    nixpkgs,
    flake-utils,
    pre-commit-hooks,
    ...
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = nixpkgs.legacyPackages.${system};
      lib = pkgs.lib;
    in {
      checks = {
        pre-commit-check = pre-commit-hooks.lib.${system}.run {
          src = ./.;
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
              settings.binPath = ".venv/bin/mypy";
              excludes = ["tests/.*"];
            };
          };
        };
      };
      devShell = pkgs.mkShell {
        env = {
          NIX_LD_LIBRARY_PATH = lib.makeLibraryPath (with pkgs; [
            zlib
            stdenv.cc.cc
            python311
          ]);
          NIX_LD = builtins.readFile "${pkgs.stdenv.cc}/nix-support/dynamic-linker";
        };

        packages = with pkgs; [
          python311
          uv
        ];

        shellHook = ''
          if [[ ! -d ".venv" ]]; then
            uv venv -p python  --link-mode copy
          fi
          uv sync --quiet --dev
          source .venv/bin/activate
          ${self.checks.${system}.pre-commit-check.shellHook}
        '';
      };

      # ...
    });
}
