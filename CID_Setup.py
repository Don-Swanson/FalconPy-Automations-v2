#!/usr/bin/env python3
# CID_Setup.py
# This script helps set up a new CID after provisioning by performing various configuration tasks.
# Please establish an "auth.py" file in the same directory as this script with the "clientid" and "clientsec" variables defined.
# Developed based on FalconPy examples

# Import required modules
from falconpy import APIHarnessV2
import sys
import time
import json

try:
    from auth import *
except ImportError:
    print("Error: auth.py file not found or missing required variables.")
    print("Please create an auth.py file with clientid and clientsec variables.")
    sys.exit(1)

def disable_and_delete_prevention_policies(falcon, policy_names_to_match, exclude_terms=None):
    """Find, disable, and delete prevention policies that match the given names but not the exclude terms"""
    print("Retrieving all prevention policies...")
    
    if exclude_terms is None:
        exclude_terms = []
    
    # Get all prevention policies
    response = falcon.command("queryCombinedPreventionPolicies")
    
    if response["status_code"] != 200:
        print(f"❌ Failed to retrieve prevention policies")
        print(f"Error: {response['body']['errors']}")
        return False
    
    if not response["body"]["resources"]:
        print("No prevention policies found.")
        return False
    
    # Print all found policies for debugging
    print("Found the following prevention policies:")
    for policy in response["body"]["resources"]:
        print(f"- {policy['name']} (ID: {policy['id']}) [Enabled: {policy['enabled']}]")
    
    # Find policies that match the names to delete and don't contain excluded terms
    policies_to_delete = []
    for policy in response["body"]["resources"]:
        policy_name = policy["name"]
        policy_id = policy["id"]
        
        # Skip policies with excluded terms
        should_exclude = False
        for exclude_term in exclude_terms:
            if exclude_term.lower() in policy_name.lower():
                should_exclude = True
                break
        
        if should_exclude:
            continue
        
        # Check if policy name contains any of the target strings
        for target_name in policy_names_to_match:
            if target_name.lower() in policy_name.lower():
                print(f"\nFound matching prevention policy: '{policy_name}' (ID: {policy_id})")
                policies_to_delete.append({
                    "id": policy_id, 
                    "name": policy_name,
                    "enabled": policy.get("enabled", True)
                })
                break
    
    if not policies_to_delete:
        print("\nNo matching prevention policies found to delete.")
        return False
    
    # First, disable all policies that need to be deleted
    policies_to_disable = [p for p in policies_to_delete if p["enabled"]]
    
    if policies_to_disable:
        print(f"\nDisabling {len(policies_to_disable)} prevention policies...")
        
        # Use the performPreventionPoliciesAction endpoint with the "disable" action
        # This is the method that worked in our testing
        for policy in policies_to_disable:
            print(f"Disabling prevention policy: '{policy['name']}' (ID: {policy['id']})...")
            
            action_body = {
                "ids": [policy["id"]]
            }
            
            action_response = falcon.command("performPreventionPoliciesAction", 
                                           action_name="disable", 
                                           body=action_body)
            
            if action_response["status_code"] == 200:
                print(f"✅ Successfully disabled prevention policy: '{policy['name']}'")
            else:
                print(f"❌ Failed to disable prevention policy: '{policy['name']}'")
                print(f"Error: {action_response['body']}")
    else:
        print("No policies need to be disabled.")
    
    # Wait for the disable operations to take effect
    print("\nWaiting for disable operations to take effect...")
    time.sleep(15)  # Increased wait time to 15 seconds
    
    # Verify policies are disabled before attempting to delete
    max_retries = 3
    for retry in range(max_retries):
        print(f"\nVerifying policies are disabled (attempt {retry+1}/{max_retries})...")
        
        response = falcon.command("queryCombinedPreventionPolicies")
        
        if response["status_code"] != 200:
            print(f"❌ Failed to retrieve prevention policies for verification")
            print(f"Error: {response['body']['errors']}")
            time.sleep(5)
            continue
        
        # Create a map of policy IDs to their enabled status
        policy_status = {}
        for policy in response["body"]["resources"]:
            policy_status[policy["id"]] = policy.get("enabled", True)
        
        # Check if all policies are disabled
        all_disabled = True
        for policy in policies_to_delete:
            if policy_status.get(policy["id"], True):
                all_disabled = False
                print(f"⚠️ Policy '{policy['name']}' (ID: {policy['id']}) is still enabled")
        
        if all_disabled:
            print("✅ All policies are now disabled and ready for deletion")
            break
        
        if retry < max_retries - 1:
            print(f"Some policies are still enabled. Waiting and retrying...")
            time.sleep(15)  # Wait longer between retries
    
    # Then delete the disabled policies
    deleted_count = 0
    for policy in policies_to_delete:
        # Check if the policy is actually disabled
        if policy_status.get(policy["id"], True):
            print(f"⚠️ Policy '{policy['name']}' is still enabled, cannot delete.")
            continue
            
        print(f"Deleting prevention policy: '{policy['name']}' (ID: {policy['id']})...")
        
        delete_response = falcon.command("deletePreventionPolicies", ids=policy["id"])
        
        if delete_response["status_code"] == 200:
            print(f"✅ Successfully deleted prevention policy: '{policy['name']}'")
            deleted_count += 1
        else:
            print(f"❌ Failed to delete prevention policy: '{policy['name']}'")
            print(f"Error: {delete_response['body']['errors']}")
    
    print(f"\nDeleted {deleted_count} prevention policies.")
    
    return deleted_count > 0

def get_or_create_host_group(falcon, name, group_type, assignment_rule=None):
    """Get an existing host group or create a new one if it doesn't exist"""
    print(f"Checking for host group: '{name}'...")
    
    # Check if group already exists
    response = falcon.command("queryCombinedHostGroups", filter=f"name:'{name}'")
    
    if response["status_code"] == 200 and response["body"]["resources"]:
        group_id = response["body"]["resources"][0]["id"]
        print(f"Host group already exists: {name} (ID: {group_id})")
        return group_id
    
    print(f"Creating host group: '{name}'...")
    
    # Prepare the request body based on group type
    if group_type == "staticByID":
        BODY = {
            "resources": [{
                "name": name,
                "group_type": "staticByID",
                "description": f"Static host group: {name}"
            }]
        }
    elif group_type == "dynamic" and assignment_rule:
        BODY = {
            "resources": [{
                "name": name,
                "group_type": "dynamic",
                "description": f"Dynamic host group: {name}",
                "assignment_rule": assignment_rule
            }]
        }
    elif group_type == "dynamic" and not assignment_rule:
        BODY = {
            "resources": [{
                "name": name,
                "group_type": "dynamic",
                "description": f"Dynamic host group: {name}"
            }]
        }
    else:
        print(f"❌ Invalid group type: {group_type}")
        return None
    
    # Create the host group
    response = falcon.command("createHostGroups", body=BODY)
    
    if response["status_code"] == 201:
        group_id = response["body"]["resources"][0]["id"]
        print(f"✅ Successfully created host group: {name} (ID: {group_id})")
        return group_id
    elif response["status_code"] == 409:
        # Handle the case where the group already exists (409 Conflict)
        print(f"Host group '{name}' already exists. Retrieving its ID...")
        
        # Try to get the group ID again with a more specific filter
        retry_response = falcon.command("queryCombinedHostGroups")
        
        if retry_response["status_code"] == 200:
            # Find the group with the exact name
            for group in retry_response["body"]["resources"]:
                if group["name"] == name:
                    group_id = group["id"]
                    print(f"Retrieved existing host group: {name} (ID: {group_id})")
                    return group_id
            
            print(f"❌ Could not find existing host group with name: {name}")
            return None
        else:
            print(f"❌ Failed to retrieve host groups")
            print(f"Error: {retry_response['body']['errors']}")
            return None
    else:
        print(f"❌ Failed to create host group: {name}")
        print(f"Error: {response['body']['errors']}")
        return None

def assign_group_to_prevention_policy(falcon, group_id, policy_id):
    """Assign a host group to a prevention policy"""
    print(f"Assigning host group (ID: {group_id}) to prevention policy (ID: {policy_id})...")
    
    BODY = {
        "action_parameters": [{"name": "group_id", "value": group_id}],
        "ids": [policy_id]
    }
    
    response = falcon.command("performPreventionPoliciesAction", action_name="add-host-group", body=BODY)
    
    if response["status_code"] == 200:
        print(f"✅ Successfully assigned host group to prevention policy")
        return True
    else:
        print(f"❌ Failed to assign host group to prevention policy")
        print(f"Error: {response['body']['errors']}")
        return False

def assign_group_to_sensor_update_policy(falcon, group_id, policy_id):
    """Assign a host group to a sensor update policy"""
    print(f"Assigning host group (ID: {group_id}) to sensor update policy (ID: {policy_id})...")
    
    BODY = {
        "action_parameters": [{"name": "group_id", "value": group_id}],
        "ids": [policy_id]
    }
    
    response = falcon.command("performSensorUpdatePoliciesAction", action_name="add-host-group", body=BODY)
    
    if response["status_code"] == 200:
        print(f"✅ Successfully assigned host group to sensor update policy")
        return True
    else:
        print(f"❌ Failed to assign host group to sensor update policy")
        print(f"Error: {response['body']['errors']}")
        return False

def main():
    # Prompt for Child CID
    child_cid = input("Enter the Child CID to configure: ")
    
    if not child_cid:
        print("Error: Child CID is required.")
        sys.exit(1)
    
    # Initialize the API client using APIHarnessV2
    print(f"\nInitializing Falcon API client for CID: {child_cid}...")
    try:
        falcon = APIHarnessV2(client_id=clientid, client_secret=clientsec, member_cid=child_cid)
    except NameError:
        print("Error: clientid and/or clientsec variables not defined in auth.py")
        sys.exit(1)
    
    # 1) Delete the specified Prevention Policies
    print("\n=== Step 1: Deleting Default Prevention Policies ===")
    # Use policy names and exclude terms from auth.py
    try:
        disable_and_delete_prevention_policies(falcon, policy_names_to_match, exclude_terms)
    except NameError:
        print("Warning: policy_names_to_match or exclude_terms not defined in auth.py")
        print("Using default values...")
        # Default values if not defined in auth.py
        default_policy_names = [
            "Phase 1 - initial deployment",
            "Phase 2 - interim protection",
            "Phase 3 - optimal protection"
        ]
        default_exclude_terms = ["Global"]
        disable_and_delete_prevention_policies(falcon, default_policy_names, default_exclude_terms)
    
    # 2) Create "ALL Hosts" dynamic host group
    print("\n=== Step 2: Creating 'ALL Hosts' Dynamic Host Group ===")
    all_hosts_group_id = get_or_create_host_group(
        falcon,
        "ALL Hosts",
        "dynamic",
        "hostname:*'*'"
    )
    
    if not all_hosts_group_id:
        print("Error: Failed to get or create 'ALL Hosts' group. Exiting.")
        sys.exit(1)
    
    # 3) Assign "ALL Hosts" to Prevention Policies
    print("\n=== Step 3: Assigning 'ALL Hosts' to Prevention Policies ===")
    try:
        for policy_id in prevention_policy_ids:
            assign_group_to_prevention_policy(falcon, all_hosts_group_id, policy_id)
    except NameError:
        print("Warning: prevention_policy_ids not defined in auth.py")
        print("Skipping prevention policy assignment...")
    
    # 4) Assign "ALL Hosts" to Sensor Update Policies
    print("\n=== Step 4: Assigning 'ALL Hosts' to Sensor Update Policies ===")
    try:
        for policy_id in sensor_update_policy_ids:
            assign_group_to_sensor_update_policy(falcon, all_hosts_group_id, policy_id)
    except NameError:
        print("Warning: sensor_update_policy_ids not defined in auth.py")
        print("Skipping sensor update policy assignment...")
    
    # 5) Create Sensor Uninstall groups
    print("\n=== Step 5: Creating Sensor Uninstall Host Groups ===")
    dynamic_uninstall_group_id = get_or_create_host_group(
        falcon,
        "Sensor Uninstall - Dynamic",
        "dynamic"
    )
    
    static_uninstall_group_id = get_or_create_host_group(
        falcon,
        "Sensor Uninstall - Static",
        "staticByID"
    )
    
    # 6) Assign Sensor Uninstall groups to Sensor Update Policies
    print("\n=== Step 6: Assigning Sensor Uninstall Groups to Sensor Update Policies ===")
    try:
        for policy_id in uninstall_policy_ids:
            if dynamic_uninstall_group_id:
                assign_group_to_sensor_update_policy(falcon, dynamic_uninstall_group_id, policy_id)
            
            if static_uninstall_group_id:
                assign_group_to_sensor_update_policy(falcon, static_uninstall_group_id, policy_id)
    except NameError:
        print("Warning: uninstall_policy_ids not defined in auth.py")
        print("Skipping uninstall policy assignment...")
    
    # 7) Create "N-1 Updates" group and assign to Sensor Update Policies
    print("\n=== Step 7: Creating 'N-1 Updates' Group and Assigning to Policies ===")
    n1_updates_group_id = get_or_create_host_group(
        falcon,
        "N-1 Updates",
        "dynamic"
    )
    
    if n1_updates_group_id:
        try:
            for policy_id in n1_policy_ids:
                assign_group_to_sensor_update_policy(falcon, n1_updates_group_id, policy_id)
        except NameError:
            print("Warning: n1_policy_ids not defined in auth.py")
            print("Skipping N-1 policy assignment...")
    
    print("\n=== CID Setup Complete ===")
    print(f"Successfully configured CID: {child_cid}")

if __name__ == "__main__":
    main() 