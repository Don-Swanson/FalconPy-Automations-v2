# FalconPy Automations v2

This repository is a new and improved version (v2) of [FalconPy_Automations](https://github.com/Don-Swanson/FalconPy_Automations). It contains enhanced scripts for automating CrowdStrike Falcon configuration tasks. These tools help streamline the setup and management of CrowdStrike Falcon environments, particularly for MSSPs managing multiple CIDs.

## What's New in v2

- Improved error handling and robustness
- Enhanced support for multiple CIDs
- Updated to use the latest FalconPy SDK with APIHarnessV2
- More comprehensive documentation
- Better security practices for credential management

## Scripts Overview

The repository includes the following scripts:

1. **CID_Setup.py** - Automates the setup of a new CrowdStrike Falcon CID after provisioning
2. **Create_Update_Policies.py** - Creates sensor update policies for Windows, Mac, and Linux platforms with N-1 and N-2 build settings

## Prerequisites

- Python 3.6 or higher
- FalconPy SDK installed (`pip install crowdstrike-falconpy`)
- CrowdStrike Falcon API credentials with appropriate permissions
- Access to the parent CID with permissions to manage child CIDs (for CID_Setup.py)

## Setup

1. Clone or download this repository
2. Copy the `auth.py.template` file to `auth.py`:
   ```
   cp auth.py.template auth.py
   ```
3. Edit the `auth.py` file and replace the placeholder values with your actual CrowdStrike Falcon API credentials and policy IDs:
   ```python
   # API credentials
   clientid = "YOUR_CLIENT_ID_HERE"
   clientsec = "YOUR_CLIENT_SECRET_HERE"
   
   # Your CIDs
   cids = {
       "PARENT_CID_HERE": "Parent CID Name",
       "CHILD_CID_1_HERE": "Child CID 1 Name",
   }
   
   # Policy IDs specific to your environment
   prevention_policy_ids = [
       "PREVENTION_POLICY_ID_1",
       "PREVENTION_POLICY_ID_2",
       "PREVENTION_POLICY_ID_3"
   ]
   
   # Additional configuration...
   ```

> **Security Note**: The `auth.py` file contains sensitive information and is excluded from version control via `.gitignore`. Never commit this file to a public repository.

## CID_Setup.py

### Description

This script automates the setup of a new CrowdStrike Falcon CID (Customer ID) after provisioning. It performs a series of configuration tasks to prepare the CID for use, including deleting default prevention policies, creating host groups, and assigning these groups to various policies.

### Usage

Run the script with Python:

```
python CID_Setup.py
```

The script will prompt you to enter the Child CID that you want to configure.

### Actions Performed

1. **Delete Default Prevention Policies**
   - Lists all prevention policies in the CID
   - Searches for policies containing any of these terms (excluding any with "Global" in the name):
     - "Phase 1 - initial deployment"
     - "Phase 2 - interim protection"
     - "Phase 3 - optimal protection"
   - Disables matching policies before attempting to delete them

2. **Create or Get "ALL Hosts" Dynamic Host Group**
   - Checks if a dynamic host group named "ALL Hosts" already exists
   - Creates it if it doesn't exist, or uses the existing one
   - Sets the assignment rule to `hostname:*'*'` (matches all hosts)

3. **Assign "ALL Hosts" to Prevention Policies**
   - Assigns the "ALL Hosts" group to specific prevention policies defined in auth.py

4. **Assign "ALL Hosts" to Sensor Update Policies**
   - Assigns the "ALL Hosts" group to specific sensor update policies defined in auth.py

5. **Create or Get Sensor Uninstall Host Groups**
   - Creates/gets a dynamic host group named "Sensor Uninstall - Dynamic"
   - Creates/gets a static host group named "Sensor Uninstall - Static"

6. **Assign Sensor Uninstall Groups to Sensor Update Policies**
   - Assigns both uninstall groups to specific sensor update policies defined in auth.py

7. **Create or Get "N-1 Updates" Group and Assign to Policies**
   - Creates/gets a dynamic host group named "N-1 Updates"
   - Assigns the group to specific sensor update policies defined in auth.py

### Key Features

- Excludes policies with "Global" in the name from deletion
- Disables policies before attempting to delete them (CrowdStrike requires this)
- Checks if host groups already exist and uses them if they do, making it safe to run multiple times
- Displays all found prevention policies to help with troubleshooting
- Robust error handling and verification steps
- All sensitive policy IDs are stored in auth.py, not in the script itself

## Create_Update_Policies.py

### Description

This script creates sensor update policies for Windows, Mac, and Linux platforms with N-1 and N-2 build settings in CrowdStrike Falcon.

### Usage

Run the script with Python:

```
python Create_Update_Policies.py
```

### Policy Details

The script creates the following policies:

| Platform | Policy Name | Description | Release Setting |
|----------|-------------|-------------|----------------|
| Windows | Windows N-1 Updates | Windows - Automatically update sensors to N-1 build | n-1 |
| Windows | Windows N-2 Updates | Windows - Automatically update sensors to N-2 build | n-2 |
| Mac | Mac N-1 Updates | Mac - Automatically update sensors to N-1 build | n-1 |
| Mac | Mac N-2 Updates | Mac - Automatically update sensors to N-2 build | n-2 |
| Linux | Linux N-1 Updates | Linux - Automatically update sensors to N-1 build | n-1 |
| Linux | Linux N-2 Updates | Linux - Automatically update sensors to N-2 build | n-2 |

Uninstall protection is enabled by default for all platforms (Windows, Mac, and Linux).

## Notes and Best Practices

- Always test these scripts in a non-production environment before using them in production
- The scripts use the FalconPy SDK's APIHarnessV2 class to interact with the CrowdStrike Falcon API
- Policy IDs are stored in auth.py - you must update them to match your environment
- Both scripts are designed to be idempotent - they can be run multiple times without causing issues
- If you encounter any errors, check your API credentials and permissions
- The scripts include detailed logging to help with troubleshooting

## Preparing for GitHub

To safely share this repository on GitHub:

1. Make sure your actual credentials and policy IDs are only in your local `auth.py` file
2. Add `auth.py` to your `.gitignore` file to prevent accidental commits
3. The `auth.py.template` file is safe to commit as it only contains placeholders
4. Verify no sensitive information is hardcoded in any of the scripts

## Troubleshooting

If you encounter issues:

1. Verify your API credentials in auth.py
2. Ensure you have the necessary permissions in CrowdStrike Falcon
3. Check the console output for specific error messages
4. For CID_Setup.py, verify that the policy IDs in auth.py match those in your environment

## Contributing

Contributions to improve these scripts are welcome. Please feel free to submit pull requests or open issues for any bugs or feature requests. 

## Disclaimer
As always, please review any script you find on the internet before using it. You alone are responsible for the scripts you run.