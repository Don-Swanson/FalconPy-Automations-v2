#!/usr/bin/env python3
# Create_Update_Policies.py
# This script creates sensor update policies for Windows, Mac, and Linux with N-1 and N-2 build settings.
# Please establish an "auth.py" file in the same directory as this script with the "clientid" and "clientsec" variables defined.
# Developed based on FalconPy examples

# Import APIHarnessV2 and Auth File
from falconpy import APIHarnessV2
try:
    from auth import *
except ImportError:
    print("Error: auth.py file not found or missing required variables.")
    print("Please create an auth.py file with clientid and clientsec variables.")
    exit(1)

def main():
    # Initialize the API client using APIHarnessV2
    print("Initializing Falcon API client...")
    try:
        falcon = APIHarnessV2(client_id=clientid, client_secret=clientsec)
    except NameError:
        print("Error: clientid and/or clientsec variables not defined in auth.py")
        exit(1)
    
    # Define the platforms and policy configurations
    platforms = ["Windows", "Mac", "Linux"]
    policy_configs = [
        {
            "name": "N-1 Updates",
            "description": "Automatically update sensors to N-1 build",
            "release_id": "n-1"
        },
        {
            "name": "N-2 Updates",
            "description": "Automatically update sensors to N-2 build",
            "release_id": "n-2"
        }
    ]
    
    # Create policies for each platform
    created_policies = []
    
    for platform in platforms:
        print(f"\nCreating policies for {platform}...")
        
        for config in policy_configs:
            policy_name = f"{platform} {config['name']}"
            policy_description = f"{platform} - {config['description']}"
            
            # Prepare the request body
            # All platforms (Windows, Mac, and Linux) now support uninstall_protection
            settings = {
                "release_id": config["release_id"],
                "uninstall_protection": "ENABLED"
            }
            
            BODY = {
                "resources": [
                    {
                        "name": policy_name,
                        "description": policy_description,
                        "platform_name": platform,
                        "settings": settings
                    }
                ]
            }
            
            # Create the policy using APIHarnessV2
            print(f"Creating policy: {policy_name}")
            response = falcon.command("createSensorUpdatePoliciesV2", body=BODY)
            
            # Check if the policy was created successfully
            if response["status_code"] == 201:
                policy_id = response["body"]["resources"][0]["id"]
                created_policies.append({
                    "name": policy_name,
                    "id": policy_id,
                    "platform": platform
                })
                print(f"✅ Successfully created policy: {policy_name} (ID: {policy_id})")
            else:
                print(f"❌ Failed to create policy: {policy_name}")
                print(f"Error: {response['body']['errors']}")
    
    # Print summary of created policies
    if created_policies:
        print("\n=== Summary of Created Policies ===")
        for policy in created_policies:
            print(f"{policy['platform']} - {policy['name']} (ID: {policy['id']})")
    else:
        print("\nNo policies were created.")

if __name__ == "__main__":
    main() 