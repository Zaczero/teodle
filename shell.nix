{ pkgs ? import <nixpkgs> { } }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    gnumake
    python311
    pipenv
    ffmpeg_6-headless

    # just to be safe (ffmpeg libs):
    x264 # H.264 video
    libopus # Opus audio
  ];

  shellHook = with pkgs; ''
    export LD_LIBRARY_PATH="${stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
    export PIPENV_VENV_IN_PROJECT=1
    export PIPENV_VERBOSITY=-1
    [ -v DOCKER ] && [ ! -f .venv/bin/activate ] && pipenv sync
    [ ! -v DOCKER ] && [ ! -f .venv/bin/activate ] && pipenv sync --dev
    [ ! -v DOCKER ] && exec pipenv shell --fancy
  '';
}
