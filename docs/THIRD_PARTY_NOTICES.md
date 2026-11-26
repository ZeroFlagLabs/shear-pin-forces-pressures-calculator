# Third-party notices

Original application code, documentation and newly authored icon artwork are MIT licensed. Third-party components retain their licences. The small UI glyphs are reused from the MIT-licensed ZeroFlagLabs radial-oring-calculator project. Private reference spreadsheets and legacy binaries are not included.

The Windows binary uses Python 3.13.16 (PSF licence), PySide6/Shiboken6 and Qt 6.12.0 (LGPLv3 or applicable alternative licences), and PyInstaller 6.22.3 (bootloader licence exception). The corresponding LGPLv3 and GPLv3 texts are in `licenses/`. The unused GPL-only Qt Virtual Keyboard components and optional Qt PDF image plugin/library are excluded from the build. Qt plugins and their component licences are subject to the Qt version-specific licence list.

Matching unmodified Qt and PySide6/Shiboken6 corresponding source archives are provided by the same distributor, ZeroFlagLabs, at the [radial-oring-calculator v1.0.0 release](https://github.com/ZeroFlagLabs/radial-oring-calculator/releases/tag/v1.0.0):
- [Qt 6.12.0 source](https://github.com/ZeroFlagLabs/radial-oring-calculator/releases/download/v1.0.0/qt-everywhere-src-6.12.0.tar.xz)
- [PySide6/Shiboken6 6.12.0 source](https://github.com/ZeroFlagLabs/radial-oring-calculator/releases/download/v1.0.0/pyside-setup-everywhere-src-6.12.0.tar.xz)
- [SHA-256 sums](https://github.com/ZeroFlagLabs/radial-oring-calculator/releases/download/v1.0.0/QT_SOURCE_SHA256SUMS.txt)

These are licensing and rebuild resources, not runtime downloads. For rebuilding with modified compatible LGPL libraries see [ONEFILE_REBUILD_AND_LGPL.md](ONEFILE_REBUILD_AND_LGPL.md).

References: [Qt licensing](https://doc.qt.io/qt-6/licensing.html), [Qt licences and third-party attributions](https://doc.qt.io/qt-6/licenses-used-in-qt.html), [Qt for Python licences](https://doc.qt.io/qtforpython-6/licenses.html), [Python licence](https://docs.python.org/3/license.html), [PyInstaller licence](https://pyinstaller.org/en/v6.22.3/license.html). Windows runtimes retain their own terms.

The embedded OpenSSL 3.5.9 libraries from the Python runtime are Copyright 1998-2026 The OpenSSL Authors, under Apache License 2.0; see [OPENSSL-LICENSE.txt](../licenses/OPENSSL-LICENSE.txt) and https://github.com/openssl/openssl/tree/openssl-3.5.9. Python and PyInstaller licence texts are also supplied under `licenses/`. The bundled file inventory is in [THIRD_PARTY_COMPONENTS.txt](THIRD_PARTY_COMPONENTS.txt).
