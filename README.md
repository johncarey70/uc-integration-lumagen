# Lumagen Radiance Pro Integration for Unfolded Circle Remotes

## ⚠️ Disclaimer ⚠️


This software may contain bugs that could affect system stability. Please use it at your own risk!


This integration driver allows control of a **Lumagen Radiance Pro** video processor connected via a Global Caché IP2SL device. A media player and remote entity are exposed to the Remote Two/3 core.

Supported **media player** attributes:

- State (active, standby, unknown)

Supported **media player** commands:

- Select source

Supported **remote** UI:

- Power on
- Power off
- Directional pad
- Numeric keypad
- Source aspect ratio presets
- Memory banks and configuration commands


## Lumagen Device Configuration Prerequisites

Before using this integration, the following settings must be applied directly on your Lumagen Radiance Pro device:

1. Navigate to: `MENU → Other → I/O Setup → RS-232 Setup`
2. Apply these settings:
   - **Echo**: On  
   - **Delimiters**: On  
   - **Report mode changes**: Fullv4
3. Be sure to **Save** your settings on the device.

These settings ensure the Lumagen device correctly echoes commands, formats responses, and reports state changes in a compatible way.

## Installation

### Run on the remote as a custom integration driver

#### 1 - Download Integration Driver
Download the uc-intg-lumagen-x.x.x-aarch64.tar.gz archive in the assets section from the [latest release](https://github.com/johncarey70/uc-integration-lumagen/releases/latest).

#### 2 - Upload & Installation
Upload in the Web Configurator
Go to Integrations in the top menu. On the top right click on Add new/Install custom and choose the downloaded tar.gz file.

#### 3 - Configuration
Click on the Integration to run setup. The player should be found automatically, if not use the manual setup.

#### 4 - Updating
First remove the existing version by clicking the delete icon on the integration, this needs to be done twice. The first time deletes the configuration, the second time fully removes it. Then repeat the above steps.

### Run on a local server
The are instructions already provided by unfolded circle in their included integrations, there is a docker-compile.sh in the repository that is used to build the included tar file.

## License

Licensed under the [**Mozilla Public License 2.0**](https://choosealicense.com/licenses/mpl-2.0/).  
See [LICENSE](LICENSE) for more details.
