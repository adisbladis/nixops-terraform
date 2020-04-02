{ pkgs ? import <nixpkgs> {

  overlays = [
    (import ../../nix-community/poetry2nix/overlay.nix)
  ];

} }:

let
  pythonEnv = pkgs.poetry2nix.mkPoetryEnv {
    projectDir = ./.;
  };

in pkgs.mkShell {
  buildInputs = [
    pkgs.terraform-full
    pkgs.poetry
    pythonEnv
  ];
}
