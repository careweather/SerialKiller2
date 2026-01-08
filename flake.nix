{
  description = "BeagleBone SerialKiller + GNU Screen flake";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = import nixpkgs { inherit system; };

      pythonDeps = pkgs.python313.withPackages (ps: with ps; [
        # Python dependencies required by SerialKiller
        pyqt6
        termcolor
        pygit2
        numpy
        pyqtgraph
        pyserial
      ]);

      serialKillerApp = pkgs.writeShellApplication {
        name = "serialkiller";
        runtimeInputs = [ pythonDeps ];
        text = ''
          # Run SerialKiller from the flake root
          python3 ./SK.py "$@"
        '';
      };
    in {
      devShells.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          pythonDeps
          screen # screen /dev/ttyUSB0 115200
          minicom # minicom -b 115200 -D /dev/ttyUSB0
          picocom # picocom -b 115200 /dev/ttyUSB0
        ];
        shellHook = ''
          echo ""
          echo "Plug both the mini USB cable and the serial pin cable from the BeagleBone into available USB ports on this computer"
          echo -e "Run the commands \033[0;34msudo dmesg | tail\033[0m or \033[0;34mls /dev/ttyUSB*\033[0m to see what device name the BeagleBone was assigned to"
          echo ""
          echo "-- BEAGLEBONE SERIAL COMMUNICATION TOOLS --"
          echo ""
          echo -e "GNU Screen is provided for TTY usage on the device: \033[0;34mscreen /dev/ttyUSB0 115200\033[0m"
          echo -e "Use \033[0;32mCtrl+A\033[0m, followed by \033[0;32mK\033[0m to kill the GNU Screen window"
          echo -e "Alternatively, SerialKiller can be used: \033[0;34mpython3 SK.py\033[0m"
          echo -e "\033[0;34mminicom\033[0m and \033[0;34mpicocom\033[0m are also provided for convenience"
          echo ""
          echo "-- HOW TO COPY A FILE TO THE BEAGLEBONE --"
          echo ""
          echo -e "(Optional) Print out a checksum of the file on the host (to verify with later): \033[0;34msha256sum your_file\033[0m"
          echo -e "Encode it in base64 (on the host): \033[0;34mbase64 your_file > your_file.b64\033[0m"
          echo -e "Begin a base64 decode/file write from STDIN on the BeagleBone (in the TTY): \033[0;34mcat | base64 -d > your_file\033[0m"
          echo ""
          echo "With the cat command waiting, paste the file contents in."
          echo "GNU Screen makes this easy, especially for large files:"
          echo -e "  1. Press \033[0;32mCtrl+A\033[0m followed by \033[0;32m:\033[0m (colon) to enter the screen command prompt."
          echo -e "  2. Type \033[0;34mreadreg p /path/to/your_file.b64\033[0m and press \033[0;32mEnter\033[0m."
          echo -e "  3. Press \033[0;32mCtrl+A\033[0m followed by \033[0;32m:\033[0m again."
          echo -e "  4. Type \033[0;34mpaste p\033[0m and press \033[0;32mEnter\033[0m."
          echo ""
          echo -e "After the text has finished scrolling, press \033[0;32mCtrl+D\033[0m to signal the end of the input to the cat command."
          echo -e "The base64 data was automatically decoded back into binary data as it came in."
          echo -e "(Optional) Verify that the BeagleBone's file's checksum matches the original: \033[0;34msha256sum your_file\033[0m"
          echo -e "           If the output of that command matches the one from the first step, you're good to go!"
          # echo -e "Decode the received file: \033[0;34mbase64 -d your_file.b64 > your_file\033[0m"
        '';
      };

      packages.default = serialKillerApp;
      apps.default = flake-utils.lib.mkApp { drv = serialKillerApp; };
    });
}

