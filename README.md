# XP-Luna for Cinnamon

Windows XP Luna Blue for Cinnamon 6.x: XP's window borders (title bar, frame and caption buttons), plus Luna push buttons, checkboxes, radio buttons, scrollbars, tabs, menus, drop-down lists, text fields and other controls in GTK 3 applications. Other widgets, GTK 4/libadwaita apps and GTK 2 apps keep the base theme's look (Adwaita by default).

Everything is drawn from Windows XP's own theme file, `luna.msstyles`, which you supply from an XP install (`C:\WINDOWS\Resources\Themes\Luna\luna.msstyles`). The build renders its parts the way XP's theme engine does. This repository contains no Microsoft files. See [Legal](#legal).

## Build

With Python 3 (the build creates a venv with Pillow in `xp-luna-for-mint/build/venv`):

```sh
xp-luna-for-mint/build.sh --msstyles /path/to/luna.msstyles    # → xp-luna-for-mint/build/XP-Luna-for-Mint
```

Or with Docker (BuildKit, the default since Docker 23):

```sh
./docker-build.sh --msstyles /path/to/luna.msstyles    # → dist/XP-Luna-for-Mint
```

The Docker build leaves no image or container behind. `luna.msstyles` (and `Windows Classic.theme` for XP-Classic) is only bind-mounted while its theme builds, so it isn't stored in any layer. Docker's build cache does keep a copy of the built theme; `docker builder prune` clears it.

Options:
- `XP_MSSTYLES=/path/to/luna.msstyles` can be set instead of `--msstyles`.
- `--base NAME` (or `$XP_BASE`) sets the theme used for everything XP-Luna doesn't style. The default is Adwaita, GTK's built-in theme, so nothing else needs to be installed. `build.sh` also accepts a theme folder. In Docker, only GTK's built-in themes are available (Adwaita, Adwaita-dark, HighContrast, HighContrastInverse).

## Install

```sh
rm -rf ~/.local/share/themes/XP-Luna-for-Mint
cp -r dist/XP-Luna-for-Mint ~/.local/share/themes/    # or xp-luna-for-mint/build/XP-Luna-for-Mint
```

Then choose it: *System Settings → Themes → Applications → XP-Luna-for-Mint*. Cinnamon 6 draws window borders with the Applications theme too.

For the closest match to XP, also set:
- **Button layout:** `gsettings set org.cinnamon.desktop.wm.preferences button-layout ':minimize,maximize,close'`
- **Scrollbars:** turn off overlay scrollbars (*Themes → Settings → Use overlay scroll bars*).
- **Title font:** `gsettings set org.cinnamon.desktop.wm.preferences titlebar-font 'Trebuchet MS Bold 10'`, with Microsoft's core fonts installed (`ttf-mscorefonts-installer`).

## XP-Classic

`xp-classic-for-mint/` builds a second theme, XP-Classic-for-Mint: Windows XP's *Windows Classic style*. It styles the same windows and widgets as XP-Luna; what is still unverified against real XP is listed in `TODO.md`. Classic has no bitmaps: Windows draws it from a colour scheme, which the build reads from XP's `Windows Classic.theme` (`C:\WINDOWS\Resources\Themes`):

```sh
xp-classic-for-mint/build.sh --scheme "/path/to/Windows Classic.theme"    # → xp-classic-for-mint/build/XP-Classic-for-Mint
./docker-build.sh --scheme "/path/to/Windows Classic.theme"               # or in Docker → dist/XP-Classic-for-Mint
```

Install it like XP-Luna (`cp -r xp-classic-for-mint/build/XP-Classic-for-Mint ~/.local/share/themes/`). For XP's text, set the desktop font to Tahoma 8 if you have it (Cinnamon: System Settings → Fonts); the theme only names the scheme's caption font for titles.

Its glyphs are drawn by the build tool, and it reads no Microsoft fonts or bitmaps. (`xp-classic-for-mint/test/synthetic.theme` is a fake scheme for the tests, not XP's colours.)

`shared/` holds the code both themes use.

## Legal

**Not affiliated with Microsoft.** This is an independent project, not made, endorsed or supported by Microsoft. Microsoft, Windows and Windows XP are trademarks of Microsoft Corporation; "Luna" is Windows XP's name for its visual style. They are used here only to describe what the theme imitates.

**What this repository contains:** only original code and documentation, under the MIT license (`LICENSE`). It contains no Microsoft files, bitmaps or extracted artwork, and downloads none. The theme takes all its artwork and colours from your `luna.msstyles`, with two exceptions written into the code: Windows XP's default tooltip colours, and the shapes of two tiny menu glyphs (a 7×7 check mark and a 4×4 bullet), redrawn by hand. The tests also use a few XP colour values as backgrounds and sample colours.

**What it builds:** the build reads a `luna.msstyles` that you supply and writes a theme containing Microsoft's copyrighted artwork. Use only a `luna.msstyles` from a copy of Windows XP you are licensed to use. The MIT license covers the build tool, not the built theme, and every built theme carries a `NOTICE` file saying so.

**Distribution of the built theme:** the built theme (`xp-luna-for-mint/build/XP-Luna-for-Mint`, `dist/XP-Luna-for-Mint`, or any copy of it) is for your own personal use only. Microsoft owns the artwork in it, and nothing in this project gives you the right to redistribute that artwork. Do not:
- upload it to theme sites (such as Cinnamon Spices or gnome-look/Pling), file hosts or chat;
- include it in packages, repositories, distributions, container images or VM images;
- commit it, or `luna.msstyles`, to any repository, public or private;
- sell it or bundle it with anything else.

You may share the build tool itself under the MIT license, so that others can build their own copy from their own `luna.msstyles`.

**XP-Classic** contains no Microsoft artwork: only colour and size values read from your `Windows Classic.theme`, and glyphs drawn by the build tool. The same non-affiliation applies. Check with someone qualified before you distribute a built copy.

You are responsible for how you use the tool and what you build with it. This section is not legal advice.
