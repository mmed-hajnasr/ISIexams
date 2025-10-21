{
  description = "A Nix-flake-based Python development environment using uv";

  inputs.nixpkgs.url = "https://flakehub.com/f/NixOS/nixpkgs/0.1";

  outputs =
    inputs:
    let
      supportedSystems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forEachSupportedSystem =
        f:
        inputs.nixpkgs.lib.genAttrs supportedSystems (
          system:
          f {
            pkgs = import inputs.nixpkgs { inherit system; };
          }
        );

      pythonVersion = "3.11";
    in
    {
      devShells = forEachSupportedSystem (
        { pkgs }:
        let
          concatMajorMinor =
            v:
            pkgs.lib.pipe v [
              pkgs.lib.versions.splitVersion
              (pkgs.lib.sublist 0 2)
              pkgs.lib.concatStrings
            ];

          python = pkgs."python${concatMajorMinor pythonVersion}";
        in
        {
          default = pkgs.mkShell {
            venvDir = ".venv";

            packages =
              with pkgs;
              [
                uv
                ruff
                pyright
                stdenv.cc.cc.lib
                zlib
                zlib.dev
                openssl
                openssl.dev
                libffi
                libffi.dev

                # Build tools for PyInstaller and cross-compilation
                gcc
                binutils
                patchelf
                file
                zip
                unzip
                wine
                wine64

                # WeasyPrint dependencies
                glib
                cairo
                pango
                gdk-pixbuf
                harfbuzz
                fontconfig
                freetype
                gobject-introspection
                gtk3
                librsvg

                # Additional dependencies for zopfli and other native extensions
                cmake
                pkg-config
                python311Packages.setuptools
                python311Packages.wheel
                python311Packages.cython
              ]
              ++ [ python ];

            shellHook = ''
              export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.zlib.out}/lib:${pkgs.openssl.out}/lib:${pkgs.libffi.out}/lib:${pkgs.glib.out}/lib:${pkgs.cairo.out}/lib:${pkgs.pango.out}/lib:${pkgs.gdk-pixbuf.out}/lib:${pkgs.harfbuzz.out}/lib:${pkgs.fontconfig.lib}/lib:${pkgs.freetype.out}/lib:${pkgs.gobject-introspection}/lib:${pkgs.gtk3.out}/lib:${pkgs.librsvg.out}/lib:${python}/lib:$LD_LIBRARY_PATH"

              # Set additional environment variables for PyInstaller
              export PYTHONPATH="${python}/lib/python${pythonVersion}/site-packages:$PYTHONPATH"
              export PKG_CONFIG_PATH="${pkgs.openssl.dev}/lib/pkgconfig:${pkgs.libffi.dev}/lib/pkgconfig:${pkgs.zlib.dev}/lib/pkgconfig:$PKG_CONFIG_PATH"

              # Create virtual environment if it doesn't exist
              if [ ! -d "$PWD/.venv" ]; then
                echo "Creating virtual environment..."
                ${python}/bin/python -m venv .venv
              fi

              # Activate virtual environment
              source .venv/bin/activate

              # Install dependencies using uv if requirements.txt exists and has changed
              if [ -f "requirements.txt" ]; then
                current_hash=$(sha256sum requirements.txt | cut -d' ' -f1)
                stored_hash=""
                if [ -f ".venv/.deps-installed" ]; then
                  stored_hash=$(cat .venv/.deps-installed)
                fi
                
                if [ "$current_hash" != "$stored_hash" ]; then
                  echo "Requirements have changed. Installing dependencies with uv..."
                  uv pip install -r requirements.txt
                  echo "$current_hash" > .venv/.deps-installed
                fi
              fi

              # Warn about Python version mismatch
              venvVersion="$(.venv/bin/python -c 'import platform; print(platform.python_version())')"
              if [ "$venvVersion" != "${python.version}" ]; then
                echo "Warning: Python version mismatch: [$venvVersion (venv)] != [${python.version}]"
                echo "         Delete '.venv' and reload to rebuild for version ${python.version}"
              fi
            '';
          };
        }
      );
    };
}
