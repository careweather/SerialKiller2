{
  lib,
  stdenv,
  python313,
  qt6,
  copyDesktopItems,
  makeDesktopItem,
  gitBranch ? "unknown",
  gitTarget ? "unknown",
  gitDate ? "unknown",
}:
let
  pythonEnv = python313.withPackages (
    ps: with ps; [
      pyqt6
      termcolor
      pygit2
      numpy
      pyqtgraph
      pyserial
    ]
  );
in
stdenv.mkDerivation {
  pname = "serialkiller";
  version = "unstable";

  src = lib.cleanSourceWith {
    src = lib.cleanSource ./.;
    filter = path: _type: baseNameOf path != "SK-GIF.gif";
  };

  nativeBuildInputs = [
    copyDesktopItems
    qt6.wrapQtAppsHook
  ];

  buildInputs = [
    pythonEnv
    qt6.qtbase
  ];

  desktopItems = [
    (makeDesktopItem {
      name = "serialkiller";
      desktopName = "Serial-Killer2";
      comment = "Serial interface program";
      exec = "serialkiller";
      icon = "serialkiller";
      terminal = false;
      categories = [
        "Development"
        "Utility"
      ];
      startupWMClass = "serialkiller";
    })
  ];

  dontBuild = true;
  dontWrapQtApps = true;

  installPhase = ''
    runHook preInstall

    share=$out/share/serialkiller
    mkdir -p "$share"

    cp SK.py SK_*.py GUI_*.py "$share/"
    cp readme.md "$share/"
    cp -r img resources doc ui_files scripts extensions "$share/"
    rm -f "$share/img/SK-GIF.gif"

    mkdir -p "$share/settings" "$share/logs"
    cp settings/empty.json "$share/settings/"
    cp logs/example.txt "$share/logs/" 2>/dev/null || true

    install -Dm644 img/SK_Icon.png $out/share/icons/hicolor/480x480/apps/serialkiller.png

    mkdir -p $out/bin
    cat > $out/bin/serialkiller <<EOF
    #!${stdenv.shell}
    export SERIALKILLER_STATE="\''${SERIALKILLER_STATE:-\''${XDG_DATA_HOME:-\$HOME/.local/share}/serialkiller}"
    mkdir -p "\$SERIALKILLER_STATE/settings" "\$SERIALKILLER_STATE/scripts" "\$SERIALKILLER_STATE/logs" "\$SERIALKILLER_STATE/extensions"
    cp -n "$out/share/serialkiller/scripts/"* "\$SERIALKILLER_STATE/scripts/" 2>/dev/null || true
    cp -n "$out/share/serialkiller/extensions/"* "\$SERIALKILLER_STATE/extensions/" 2>/dev/null || true
    export SERIALKILLER_GIT_BRANCH=${lib.escapeShellArg gitBranch}
    export SERIALKILLER_GIT_TARGET=${lib.escapeShellArg gitTarget}
    export SERIALKILLER_GIT_DATE=${lib.escapeShellArg gitDate}
    exec ${pythonEnv}/bin/python $out/share/serialkiller/SK.py "\$@"
    EOF
    chmod +x $out/bin/serialkiller

    runHook postInstall
  '';

  preFixup = ''
    wrapQtApp "$out/bin/serialkiller"
  '';

  meta = {
    description = "Serial terminal with CLI-like and GUI interfaces, scripting, logging, and real-time plotting";
    longDescription = ''
      Serial Killer is a serial terminal with both CLI-like and GUI
      interfaces. It supports scripting, logging, keyboard control,
      real-time plotting, user extensions, and auto-reconnect.
    '';
    homepage = "https://github.com/careweather/SerialKiller2";
    license = lib.licenses.mpl20;
    mainProgram = "serialkiller";
    platforms = lib.platforms.unix;
  };
}
