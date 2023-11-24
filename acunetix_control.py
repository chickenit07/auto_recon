#!/usr/bin/env python3
import requests
import json
import argparse
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
acunetix_host = ""
acunetix_port = ""
acunetix_apikey = ""

def checkAcunetixConnection():
    with open("config.conf", "r") as file:
        acunetix_config = json.load(file)
        global acunetix_host
        global acunetix_port
        global acunetix_apikey
        if acunetix_config["acunetix_host"]:
            acunetix_host = acunetix_config["acunetix_host"]
        else:
            print("acunetix_host is not set.")
            return False
        if acunetix_config["acunetix_port"]:
            acunetix_port = acunetix_config["acunetix_port"]
        else:
            print("acunetix_port is not set.")
            return False
        if acunetix_config["acunetix_apikey"]:
            acunetix_apikey = acunetix_config["acunetix_apikey"]
        else:
            print("acunetix_apikey is not set.")
            return False

    url = "https://" + acunetix_host + ":" + acunetix_port + "/api/v1/target_groups"
    headers = {
        "X-Auth": acunetix_apikey
    }
    response = requests.get(url, headers=headers, verify=False)
    if response.status_code == 200:
        print("Connect to Acunetix ok!")
        return True
    else:
        print("Connetion fail.", response.status_code)
        return False

def createTargetsGroup(domain, output_path):
    url = "https://" + acunetix_host + ":" + acunetix_port + "/api/v1/target_groups"
    headers = {
        "X-Auth": acunetix_apikey
    }
    choice = input(f"Target group '{domain}' already exists. This action will delete the existing target group. Do you want to continue? (Y/n): ")
    if choice.lower() == "n":
        print("Aborted by user.")
        return 
    # Check if the target group already exists
    existing_target_group_id = getTargetGroupIdByName(domain)
    
    if existing_target_group_id:
        # Target group already exists, delete it
        deleteTargetGroup(existing_target_group_id)
        print(f"Existing target group '{domain}' deleted.")
    # Create a new target group
    data = {
        "name": domain
    }
    response = requests.post(url, headers=headers, json=data, verify=False)
    print(response.text)
    if response.status_code == 201:
        print("Create Targets Group successful!")
        response_data = response.json()
        with open(f"{output_path}/acunetix_targets_group.json", "w") as file:
            json.dump(response_data, file)
        return response_data
    else:
        print("API request failed with status code:", response.status_code)
        return None

def deleteTargetGroup(target_group_id):
    url = f"https://{acunetix_host}:{acunetix_port}/api/v1/target_groups/{target_group_id}"
    headers = {
        "X-Auth": acunetix_apikey
    }
    response = requests.delete(url, headers=headers, verify=False)

    if response.status_code == 204:
        print(f"Target group with ID {target_group_id} deleted successfully.")
    else:
        print(f"Failed to delete target group with ID {target_group_id}. Status code:", response.status_code)

def getTargetGroupIdByName(target_group_name):
    url = f"https://{acunetix_host}:{acunetix_port}/api/v1/target_groups"
    headers = {
        "X-Auth": acunetix_apikey
    }
    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        response_data = response.json()
        target_groups = response_data.get("groups", [])
        for group in target_groups:
            if group.get("name") == target_group_name:
                return group.get("group_id")
    else:
        print("Failed to retrieve target groups. Status code:", response.status_code)
    return None


def createTargets(targets_list, targets_group, output_path):
    targets = []
    for target in targets_list:
        targets.append({
            "address": target["url"],
            "description": target["status_code"] + " | " + target["title"],
            "criticality": 30
        })
    url = "https://" + acunetix_host + ":" + acunetix_port + "/api/v1/targets/add"
    headers = {
        "X-Auth": acunetix_apikey
    }
    data = {
        "targets": targets,
        "groups": [targets_group.get("group_id")]
    }
    response = requests.post(url, headers=headers, json=data, verify=False)
    if response.status_code == 200:
        print("Create Targets successfully!")
        response_data = response.json()
        with open(f"{output_path}/acunetix_targets.json", "w") as file:
            json.dump(response_data, file)
        return response_data
    else:
        print("API request failed with status code:", response.status_code)
        return None
    
def configurationTargets(targets):
    for target in targets["targets"]:
        url = "https://" + acunetix_host + ":" + acunetix_port + "/api/v1/targets/" + target["target_id"] + "/configuration"
        headers = {
            "X-Auth": acunetix_apikey
        }
        data = {
            "scan_speed": "sequential",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        response = requests.patch(url, headers=headers, json=data, verify=False)
        if response.status_code == 204:
            print("Configuration Targets successful.", target["address"]) 
        else:
            print("Configuration Targets false.", target["address"])
        url = "https://" + acunetix_host + ":" + acunetix_port + "/api/v1/targets/" + target["target_id"] + "/allowed_hosts"
        for target_temp in targets["targets"]:
            data = {
                "target_id": target_temp["target_id"]
            }
            response = requests.post(url, headers=headers, json=data, verify=False)

def activeScans(targets):
    url = "https://" + acunetix_host + ":" + acunetix_port + "/api/v1/scans"
    headers = {
        "X-Auth": acunetix_apikey
    }
    for target in targets["targets"]:
        data = {
                "target_id": target["target_id"],
                "profile_id": "11111111-1111-1111-1111-111111111111",
                "report_template_id": "11111111-1111-1111-1111-111111111111",
                "schedule": {
                    "disable": True,
                    "time_sensitive": False,
                    "history_limit": 10,
                    "start_date": None,
                    "triggerable": False
                },
                "max_scan_time": 0,
                "incremental": False
        }
        response = requests.post(url, headers=headers, json=data, verify=False)
        if response.status_code == 201:
            print("Start scan Targets successful.", target["address"]) 
        else:
            print("Start scan Targets false.", target["address"])

def checkStatus(targets_path):
    if not checkAcunetixConnection():
        return
    with open(f"{targets_path}/acunetix_targets.json", "r") as file:
        targets = json.load(file)["targets"]
    headers = {
        "X-Auth": acunetix_apikey
    }
    for target in targets:
        url = "https://" + acunetix_host + ":" + acunetix_port + "/api/v1/targets/" + target["target_id"]
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code == 200:
            print(target["address"], response.json()["last_scan_session_status"], response.json()["severity_counts"])
        else:
            print("Get Targets scan status false.", target["target_id"])

def stopScans(targets_path):
    if not checkAcunetixConnection():
        return
    with open(f"{targets_path}/acunetix_targets.json", "r") as file:
        targets = json.load(file)["targets"]
    headers = {
        "X-Auth": acunetix_apikey
    }
    for target in targets:
        url = "https://" + acunetix_host + ":" + acunetix_port + "/api/v1/targets/" + target["target_id"]
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code == 200:
            url = "https://" + acunetix_host + ":" + acunetix_port + "/api/v1/scans/" + str(response.json()["last_scan_id"]) + "/abort"
            response = requests.post(url, headers=headers, verify=False)
            print("Stop scan target", target["address"])
        else:
            print("Stop scan target fail", target["address"])

def deleteScans(targets_path):
    if not checkAcunetixConnection():
        return
    with open(f"{targets_path}/acunetix_targets.json", "r") as file:
        targets = json.load(file)["targets"]
    headers = {
        "X-Auth": acunetix_apikey
    }
    for target in targets:
        url = "https://" + acunetix_host + ":" + acunetix_port + "/api/v1/targets/" + target["target_id"]
        response = requests.delete(url, headers=headers, verify=False)
        if response.status_code == 200:
            print("Delete target", target["address"])
        else:
            print("Delete target FAIL", target["address"])
    with open(f"{targets_path}/acunetix_targets_group.json", "r") as file:
        group = json.load(file)
    url = "https://" + acunetix_host + ":" + acunetix_port + "/api/v1/target_groups/" + group["group_id"]
    response = requests.delete(url, headers=headers, verify=False)
    if response.status_code == 200:
        print("Delete group", group["name"])
    else:
        print("Delete group FAIL", group["name"])

def createScans(domain, targets, output_path):
    print("""
                                     _    _       
     /\                             | |  (_)      
    /  \    ___  _   _  _ __    ___ | |_  _ __  __
   / /\ \  / __|| | | || '_ \  / _ \| __|| |\ \/ /
  / ____ \| (__ | |_| || | | ||  __/| |_ | | >  < 
 /_/    \_\\\___| \__,_||_| |_| \___| \__||_|/_/\_\\
    """)
    if checkAcunetixConnection():
        targets_group = createTargetsGroup(domain, output_path)
        targets = createTargets(targets, targets_group, output_path)
        configurationTargets(targets)
        activeScans(targets)
    else:
        print("Connect to Acunetix server has error. Check configuration file.")

def main(args):
    print("""
                                     _    _       
     /\                             | |  (_)      
    /  \    ___  _   _  _ __    ___ | |_  _ __  __
   / /\ \  / __|| | | || '_ \  / _ \| __|| |\ \/ /
  / ____ \| (__ | |_| || | | ||  __/| |_ | | >  < 
 /_/    \_\\\___| \__,_||_| |_| \___| \__||_|/_/\_\\
 
 Using -h or --help.
    """)
    targets_path = args.targets_path
    status = args.status
    stop_scans = args.stop_scans
    delete_scans = args.delete_scans

    if status:
        checkStatus(targets_path)

    if stop_scans:
        stopScans(targets_path)

    if delete_scans:
        deleteScans(targets_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Acunetix Control")
    parser.add_argument("-t", "--targets-path", help="Path to targets (domain), acunetix_targets_group.json and acunetix_targets.json")
    parser.add_argument("-s", "--status", action="store_true", help="Check scans status")
    parser.add_argument("--stop-scans", action="store_true", help="Stop scan(s)")
    parser.add_argument("--delete-scans", action="store_true", help="Delete scan(s)")
    args = parser.parse_args()
    main(args)