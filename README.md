# Shear Pin Forces & Pressures Calculator

**v2.0.0 | ZeroFlagLabs**

A portable Windows engineering calculator for estimated minimum and maximum direct shear failure loads of identical pins and optional differential release pressures.

## Download

Download the [latest release](https://github.com/ZeroFlagLabs/shear-pin-forces-pressures-calculator/releases/latest), extract the ZIP and run the single unsigned EXE. No separate Python installation is needed.

## Features

- Live force and optional pressure results, symmetrical tolerances or limits.
- Configurable pin count, shear planes per pin and ultimate shear strength factor (default 0.6).
- Inspect Results with governing minimum/maximum cases and selectable precision.
- Copy snapshot and Save PNG generate the same calculation report.
- Reset restores neutral inputs, one plane and factor 0.6. Settings includes assumptions, references and optional GitHub update notifications.

## Engineering basis

Ultimate shear strength is estimated as factor × UTS. Total effective area is the single-plane circular pin area multiplied by the pin count and planes per pin. Minimum and maximum forces use the corresponding strength and diameter limits. Minimum pressure uses minimum force / maximum annulus area; maximum pressure uses maximum force / minimum annulus area. Minimum OD must exceed maximum ID; a zero ID is valid. Equal load sharing is assumed. The estimate excludes friction, bending, bearing, stress concentrations and other failure modes.

NASA RP-1228, Richard T. Barrett, *Fastener Design Manual*, March 1990, p. 21, provides approximate ultimate shear/tensile ratios of 0.60 for carbon and alloy steels and 0.55 for stainless steels. [Reference](https://ntrs.nasa.gov/citations/19900009424). Material-specific data and representative tests are preferable. This is not a safety factor or proof of a release-pressure window.

## Development and licensing

See [development instructions](docs/DEVELOPMENT.md), [third-party notices](docs/THIRD_PARTY_NOTICES.md) and [LGPL rebuild instructions](docs/ONEFILE_REBUILD_AND_LGPL.md). Original application code is MIT licensed.
