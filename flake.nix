{
  description = "NDC SDK Python development dependencies";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (localSystem:
      let
        pkgs = import nixpkgs
          {
            system = localSystem;
            overlays = [ ];
          };
      in

      {
        packages.${localSystem}.default = self.packages.${localSystem}.uv;

        devShells = {
          default = pkgs.mkShell {
            nativeBuildInputs = [
              # Development
              pkgs.uv 
            ];
          };
        };
      }
    );
}
