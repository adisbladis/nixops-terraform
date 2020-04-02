{ pkgs ? import <nixpkgs> {

  overlays = [
    (import ../../nix-community/poetry2nix/overlay.nix)
  ];

} }:

pkgs.poetry2nix.mkPoetryApplication {
  projectDir = ./.;

  propagatedBuildInputs = [
    pkgs.terraform-full
  ];

}
