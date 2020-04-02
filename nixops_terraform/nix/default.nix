let
  pkgs = import <nixpkgs> {};
  inherit (pkgs) lib;

in {

  config_exporters = { optionalAttrs, ... }: [
    (config: builtins.trace config.deployment {})
  ];

  options = [
  ];

  resources = { evalResources, zipAttrs, resourcesByType, ... }: {
    terraform = let
      zippedAttrs = (zipAttrs resourcesByType.terraform or []);
    in evalResources ./terraform.nix (builtins.trace (builtins.toJSON zippedAttrs) zippedAttrs);
  };

}
