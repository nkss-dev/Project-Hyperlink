{
  description = "Project Hyperlink's development environment";

  inputs = {
    python-env.url = "https://flakehub.com/f/GetPsyched/python-env/0.x.x.tar.gz";
    python-env.inputs.nixpkgs.follows = "nixpkgs";

    nixpkgs-fluent.url = "github:getpsyched/nixpkgs/python-fluent";
  };

  outputs = inputs@{ nixpkgs, python-env, ... }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      pkgs-fluent = inputs.nixpkgs-fluent.legacyPackages.${system};
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          python-env.outputs.packages.${system}.default
          python-env.outputs.packages.${system}.vscode
          railway
          pkgs-fluent.python311Packages.fluent-runtime
          (python311.withPackages (p: with p; [
            asyncpg
            black
            discordpy
            python-dotenv
            pytz
            tabulate
          ]))
        ];
      };
    };
}
