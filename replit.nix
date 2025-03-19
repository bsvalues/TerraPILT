{pkgs}: {
  deps = [
    pkgs.socat
    pkgs.netcat
    pkgs.nodejs
    pkgs.python3
    pkgs.wkhtmltopdf
    pkgs.glibcLocales
  ];
}
