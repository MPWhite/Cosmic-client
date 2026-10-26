# Cosmic client
This repository contains files and instructions on how to get started with the client for the [Cosmic MapleStory v83 server](https://github.com/P0nk/Cosmic).


## Overview

### Files
- **MapleGlobal-v83-setup.exe** - the original installer that you would download from mapleglobal.com to install the game back in the day 
- **HeavenMS-localhost-WINDOW.exe** (aka "the client") - a modified client to allow playing locally on your own server (and also containing some additional customizations)
- **cosmic-wz** - custom wz files required to play Cosmic properly (see explanation below)

> [!IMPORTANT]
> The client is flagged as a virus and will be automatically deleted by Windows Security. To work around this, you need to add your _Downloads_ and installation directories as _Exclusions_ in _Virus & threat protection settings_.

It is flagged as a virus because it's been modified for local play and other custom features. Many people have used it without issue, but use it at your own risk.

### About the wz files
Cosmic requires custom wz files due to legacy reasons. Cosmic is built on HeavenMS which customized many parts of the game. Part of this customization was wz editing (such as adjusting text, adding levels to equipment, etc.), so we are stuck with these custom wz files for now. 
However, the long term goal is to free ourselves from the custom wz files and only depend on the vanilla wz files (provided by the installer). This is an arduous process that will take some time.

### Git LFS
[Git LFS](https://git-lfs.com/) is used to store the .wz and .exe files. To get the full files when you clone the repo, you need to have Git LFS installed. You can also download the raw files individually via GitHub.

### Releases
The release versions correspond to tags in [Cosmic](https://github.com/P0nk/Cosmic). It is recommended to use the latest versions of _Cosmic-client_ and _Cosmic_ since they are tested to work together.

Releases only contain the client and the cosmic wz files. The setup/installer is excluded because it is static and will not change in between releases.

## Installation

### macOS: play in a browser

The Mac launcher builds [MapleStory WASM](https://github.com/nmnsnv/maplestory-wasm)
and connects it to your local Cosmic server. The browser runs the game; the
Windows executable is not used. Chrome is the tested browser on Apple Silicon.

Install [Homebrew](https://brew.sh), then run once in this repository:

```sh
./setup-macos.sh
```

Start `../Cosmic/launch-macos.command`, then double-click
`launch-macos.command` in this folder, or run it in Terminal. It opens
<http://127.0.0.1:8000>. Keep the server and client launcher terminals running.

For the bundled test account, log in with **admin / admin**, choose a channel,
select **Admin**, and click **Start**. Enter PIC **000000** using the keyboard or onscreen keypad;
the onscreen digits move after each click. Click inside the game to focus the keyboard.

Setup installs the build dependencies, downloads the repository's Git LFS files,
extracts the missing vanilla WZ data, converts the assets to NX, and compiles the
browser client using Emscripten 4.0.21. Allow about 20 GB of free space for a fresh
checkout and setup. Subsequent runs reuse unchanged assets and build outputs.
All downloaded tools, generated assets, and build output stay in `.local/`.
Original WZ files are read-only inputs.

The source revisions are pinned in `setup-macos.sh`. Patches in `macos/patches/`
make the converter work on macOS and adapt the browser client to the supplied
v83 UI. The UI patch restores login/character screens, the HUD and chat, NPC
dialogs, inventory/equipment/stats/skills, maps, shops/storage and quantity
prompts. It also aligns browser rendering with mouse coordinates, restores
keyboard/PIC focus, prevents input from reaching windows behind a modal, and
shows server rejection messages and connection recovery controls.
The Cash Shop uses the classic artwork already in the supplied `UI.nx`;
this installation does not require a separate `UI_83.nx` download.
A newer `UI.wz` is not required for this setup. This is an alternative client under
active development; some menus and gameplay features differ from the Windows
client. It is not a complete recreation of every original feature.

After updating the patches, rerun `./setup-macos.sh` and refresh the browser.
Setup supports both a fresh checkout and one with the earlier bootstrap patch.
For native regression checks against the actual converted v83 assets, run:

```sh
./macos/verify-browser-ui.sh
```

The check creates read-only asset symlinks under `.local/ui-test-assets` and
runs the upstream C++ test suite plus compatibility regressions. CMake needs
FreeType for these optional native tests (`brew install freetype` if missing).
The UI repair was also tested in Chrome: PIC login, NPC Next/Back/cancel and
quest acceptance, core windows, scaled mouse input, shop purchase quantities,
storage deposits/withdrawals, reconnecting, and modal input protection.
Native tests do not replace gameplay testing.

Known gaps remain in this alternative client: MTS/reporting, inventory expansion
and dropping mesos, and specialized NPC appearance/quiz/dimensional-mirror
windows. Unavailable controls are hidden/disabled, and unsupported NPC dialog
types show a closable message. These are not implemented by the UI patch.

The web server uses port **8000**, the game WebSocket bridge **8080**, and asset
streaming **8765**, all bound to `127.0.0.1`. Cosmic's login server must be running
on port **8484**. Use `stop-macos.command` or Control-C in the client terminal to
stop the browser services. The Cosmic server and saved characters are separate.
Diagnostics are in `.local/browser.log` and `.local/asset-*.log`.
Set `COSMIC_NO_BROWSER=1` to start the services without opening a browser tab.

### Play on a phone with Tailscale

Connect this Mac and your phone to Tailscale, then double-click
`play-mobile.command`. It starts the installed services and prints a private
HTTPS link. Open it in Safari or Chrome and turn the phone sideways. The same
account and characters work on desktop and mobile; log out on one device before
using the other. Keep the Mac connected with its lid open while playing. The
launcher prevents idle sleep while the browser service runs.

The game renders at the phone's aspect ratio, filling the available screen
without stretching character artwork. Rotation updates the camera, HUD and tap
coordinates. Touch controls sit above the status bar and quickslots.
Use **Full screen** on supported browsers. On iPhone, use **Share → Add to Home
Screen**, enable **Open as Web App** if shown, and launch that Home Screen icon
to remove the browser address bar. Close the original game tab before signing
in from the Home Screen app. The Full screen button also shows these steps when
the browser cannot enter fullscreen directly.

The mobile client provides touch movement/action buttons and native text entry
for login, PIC, chat and NPC prompts. Assets load as needed, so the first visit
can take longer. Current Safari/Chrome is recommended.

The launcher uses Tailscale Serve on HTTPS ports 8443 (page), 8444 (game), and
8445 (assets). It preserves existing services on other ports and does not enable
Funnel. Local services remain bound to loopback; the game bridge accepts only
the local login server and the three configured channels. To remove phone access:

```sh
tailscale serve --https=8443 off
tailscale serve --https=8444 off
tailscale serve --https=8445 off
```

The original Windows client was also tested with several Wine versions on Apple
Silicon and failed during initialization. The Mac scripts use the browser client
because that route can be built from source and tested locally.

### Windows guide
1. Run _MapleGlobal-v83-setup.exe_ and install in a directory of your choice or use the default location (C:\Nexon\MapleStory)
2. Remove the following files from the installation directory: 
   - _HShield_ (remove the entire directory)
   - _ASPLnchr.exe_
   - _MapleStory.exe_
   - _Patcher.exe_
3. Copy all the wz files from _cosmic-wz_ (_Character.wz_, _Etc.wz_, _Item.wz_, etc.) into the installation directory and replace.
4. Copy the client into the installation directory.
5. Done! Double-click the client to start the client. 
   - The server has to be running. If it's not running, you will see "We are unable to connect to the login server (...)".

### Troubleshooting
The client sometimes has trouble starting. If you see "Client connected (...)" in the server logs, but the client doesn't boot up or shows an error message, try spam double-clicking the client. If you're in luck, at least one client will start successfully.

## Client editing

### Client customizations
For more information about the client and its features, see [HeavenMS on GitHub](https://github.com/ronancpl/HeavenMS#download-items).

Some notable features:
* Opens in window mode by default
* Uncapped max speed

### Edit client ip
1. Download and install a hex editor: [HxD](https://mh-nexus.de/en/hxd/)
2. Start HxD and open your client exe (I recommend making a copy of it first). At this point you should see a bunch of hex codes and a "Decoded text" column to the right of it.
3. Ctrl+f and search for Text-string "127.0.0.1". You should find three occurrences right above each other.
4. Place your cursor before the first "127" and start typing the desired ip, overwriting what is already there. Do the same on the other two and click on Save.
5. Done! Now the client will attempt to connect to that ip address instead when you launch it.



