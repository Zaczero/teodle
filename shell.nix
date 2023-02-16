{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python311
    pipenv
  ];

  shellHook = ''
    export PIPENV_VENV_IN_PROJECT=1
    export PIPENV_VERBOSITY=-1
    ${pkgs.pipenv}/bin/pipenv install --ignore-pipfile
    source .venv/bin/activate
  '';
}
