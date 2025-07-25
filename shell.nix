{
  pkgs ? import <nixpkgs> { },
}:

pkgs.mkShellNoCC {
  nativeBuildInputs = with pkgs; [
    openjdk # https://github.com/NixOS/nixpkgs/issues/428214
    postgresql
    railway
    (python3.withPackages (
      py-pkgs: with py-pkgs; [
        asyncpg
        discordpy
        fluent-runtime
        fluent-pygments
        google-api-python-client
        google-auth-httplib2
        google-auth-oauthlib
        python-dotenv
        pytz
        tabula-py
        tabulate
      ]
    ))
  ];
}
