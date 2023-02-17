{ pkgs ? import <nixpkgs> { } }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python311
    pipenv
    yt-dlp
  ];

  shellHook = ''
    export PIPENV_VENV_IN_PROJECT=1
    export PIPENV_VERBOSITY=-1
    pipenv install --dev --ignore-pipfile
    source .venv/bin/activate
  '';
}
