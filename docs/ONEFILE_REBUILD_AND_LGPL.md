# One-file build and LGPL replacement

The portable ZIP contains one unsigned EXE. PyInstaller extracts its bundled runtime and Qt dynamic libraries into a temporary directory at launch. Libraries are not separately replaceable next to the EXE.

The tagged public application source and build script are available under MIT. Matching Qt/PySide6 sources and licence information are linked from [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). To rebuild with modified libraries, build compatible Qt and PySide6/Shiboken6 libraries from those sources, use a clean Windows Python 3.13.16 environment with the ABI-compatible modified libraries installed in place of the stock wheel libraries, then invoke the same build script as documented in [DEVELOPMENT.md](DEVELOPMENT.md). The build collects the selected environment's runtime libraries. No publisher-only signing key or installation privilege is required. Recipients may modify and debug the libraries and recombine the application under the applicable licences. Preserve required component notices. The modified-library rebuild route is documented; a separate modified-Qt compilation was not performed for this release.

The normal user needs only the distribution ZIP; no Python install or source archives are required to run the program.
