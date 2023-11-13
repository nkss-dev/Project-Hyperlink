{
  description = "Project Hyperlink's development environment";

  inputs = {
    flakey-devShells.url = "https://flakehub.com/f/GetPsyched/not-so-flakey-devshells/0.x.x.tar.gz";
    flakey-devShells.inputs.nixpkgs.follows = "nixpkgs";

    nixpkgs-fluent.url = "github:getpsyched/nixpkgs/python-fluent";
  };

  outputs = inputs@{ nixpkgs, flakey-devShells, ... }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      pkgs-fluent = inputs.nixpkgs-fluent.legacyPackages.${system};
      flakey-devShell-pkgs = flakey-devShells.outputs.packages.${system};
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        nativeBuildInputs = with pkgs; [
          (flakey-devShell-pkgs.default.override { environments = [ "nix" "python" ]; })
          (flakey-devShell-pkgs.vscodium.override { environments = [ "nix" "python" ]; })

          railway
          pkgs-fluent.python311Packages.fluent-runtime
          (python311.withPackages (p: with p; [
            asyncpg
            black
            discordpy
            google-api-python-client
            google-auth-httplib2
            google-auth-oauthlib
            python-dotenv
            pytz
            tabulate
          ]))
        ];
      };
    };
}
