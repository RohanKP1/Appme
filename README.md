# Appme

A modern, GNOME-integrated utility to run your favorite websites as if they were native desktop applications. Inspired by the excellent Linux Mint Webapp Manager, rebuilt for GTK4/Libadwaita.

## Features
* **Native Look & Feel:** Built with GTK4 and Libadwaita for seamless GNOME integration.
* **Smart Browser Detection:** Automatically finds and utilizes installed browsers (System, Flatpak, and Snap).
* **Automatic Icon Fetching:** Instantly searches your system's icon theme to match web apps to native icons.
* **Broad Engine Support:** Supports Chromium-based browsers, Firefox, and GNOME Web (Epiphany).

## Project Structure
```
.
├── data
│   ├── icons
│   │   ├── appme-icon-128.png
│   │   ├── appme-icon-256.png
│   │   ├── appme-icon-48.png
│   │   ├── appme-icon-512.png
│   │   ├── appme-icon-64.png
│   │   └── appme-icon.png
│   ├── io.github.rohankp1.Appme.desktop
│   └── io.github.rohankp1.Appme.png
├── LICENCE
├── README.md
└── src
    ├── desktop_entry.py
    └── main.py
```

## License
This project is licensed under the GNU General Public License v3.0 (GPL-3.0).