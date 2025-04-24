# Lumagen Radiance Pro Integration for Remote Two/3

**Disclaimer**: Use at your own risk. This integration is currently **untested** and in active development. It has not yet been verified with real hardware still awaiting delivery of the R3 Remote.

This integration driver allows control of a **Lumagen Radiance Pro** video processor connected via a Global Caché IP2SL device. A media player and remote entity are exposed to the Remote Two/3 core.

Supported **media player** attributes:

- State (active, standby, unknown)

Supported **media player** commands:

- Power on
- Power off
- Toggle power
- Select source

Supported **remote** UI:

- Power on
- Power off
- Toggle power
- Directional pad
- Numeric keypad
- Source aspect ratio presets
- Memory banks and configuration commands

## Usage

### Setup

- If you want to try this, install via upload uc-intg-lumagen-aarch64.tar.gz in Integrations.


### Lumagen Device Configuration Prerequisites

Before using this integration, the following settings must be applied directly on your Lumagen Radiance Pro device:

1. Navigate to: `MENU → Other → I/O Setup → RS-232 Setup`
2. Apply these settings:
   - **Echo**: On  
   - **Delimiters**: On  
   - **Report mode changes**: Fullv4
3. Be sure to **Save** your settings on the device.

These settings ensure the Lumagen device correctly echoes commands, formats responses, and reports state changes in a compatible way.

## License

Licensed under the [**Mozilla Public License 2.0**](https://choosealicense.com/licenses/mpl-2.0/).  
See [LICENSE](LICENSE) for more details.
