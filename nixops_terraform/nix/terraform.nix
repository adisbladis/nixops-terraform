{ lib, ... }:

{

  options = {

    resource = lib.mkOption {
      default = {};
      type = lib.types.attrs;
      description = "Terraform resources in (JSON style).";
    };

  };

  config._type = "terraform";
}
