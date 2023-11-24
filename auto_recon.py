#!/usr/bin/env python3
import json
import argparse
import acunetix_control
import requests
import os
import shutil
import subprocess

def checkOsmedeusConnection():
    with open("config.conf", "r") as file:
        config = json.load(file)
        global osmedeus_host
        global osmedeus_port
        global osmedeus_raw_path
        if config["osmedeus_host"]:
            osmedeus_host = config["osmedeus_host"]
        else:
            print("osmedeus_host is not set.")
            return False
        if config["osmedeus_port"]:
            osmedeus_port = config["osmedeus_port"]
        else:
            print("osmedeus_port is not set.")
            return False
        if config["osmedeus_raw_path"]:
            osmedeus_raw_path = config["osmedeus_raw_path"]
        else:
            print("osmedeus_raw_path is not set.")
            return False
    url = "https://" + osmedeus_host + ":" + osmedeus_port + "/" + osmedeus_raw_path + "/workspaces/"

    response = requests.get(url, verify=False)
    if response.status_code == 200:
        print("Connect to Osmedeus ok!")
        return True
    else:
        print("Connetion fail.", response.status_code)
        return False
    
def runOsmedeusCommand(target):
    command = f"osmedeus scan -f general -t {target}"
    process = subprocess.run(command, shell=True)
    return process

def runOsmedeus(domain, subdomain_file):
    if checkOsmedeusConnection():
        print("Start running Osmedeus")
        try:
            #Run osmedeus
            runOsmedeusCommand(domain)
            print("Run Osmedeus Successfully")
            return True
        except KeyboardInterrupt as e:
            # Handle the specific exception
            print(f"Exception: {e}")
            if os.path.exists(subdomain_file):
                return True
            return False
        except Exception as e:
            # Catch other exceptions
            print(f"Unexpected Exception: {e}")
            return False

def runHttpxCommand(subdomain_file):   

    command = f"cat {subdomain_file} | /root/go-workspace/bin/httpx --no-color -title -status-code | tee {httpx_file}"
    print(command)

    try:
        #Run httpx command
        result = subprocess.run(command, shell=True)
        print(result)
        return True
    except subprocess.CalledProcessError:
        # The command failed (non-zero return code)
        return False

def process_httpx_file(filename):
    result = []
    with open(filename, "r", encoding="utf-8") as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if line:
                parts = line.split()
                url = parts[0]
                status_code = parts[1].strip("[]")
                title = ' '.join(parts[2:]).strip("[]")
                result.append({
                    "url": url,
                    "status_code": status_code,
                    "title": title
                })
    return result

def runAcunetix():
        targets = process_httpx_file(httpx_file)
        print(targets)
        acunetix_control.createScans(domain, targets, output_path)

def checkDirExist(output_path):
     # Check if the output path exists
    if os.path.exists(output_path):
        # Ask the user whether to continue or not
        choice = input(f"The output path '{output_path}' already exists. This action will delete the existing directory and its contents. Do you want to continue? (Y/n): ")
        if choice.lower() == "n":
            print("Aborted by user.")
            return 

        # Remove the existing directory
        shutil.rmtree(output_path)
        print(f"Deleted existing directory: {output_path}")

    # Create a new directory
    os.makedirs(output_path)
    print(f"Created new directory: {output_path}")

def main(args):
    global domain
    global httpx_file
    global output_path
    global osmedeus_local_dir

    domain = args.domain
    output_path = args.output or "/tmp"
    acunetix = args.acunetix

    osmedeus_local_dir = "/root"
    httpx_file = output_path + "/" + domain + "/httpx.txt"
    output_path = f"{output_path}/{domain}"
    
    subdomain_file = osmedeus_local_dir + "/workspaces-osmedeus/"  + domain + "/subdomain/" + "final-" + domain + ".txt"

    checkDirExist(output_path)
    if runOsmedeus(domain, subdomain_file) and runHttpxCommand(subdomain_file) and acunetix:
        print("Start running Acunetix")
        runAcunetix()
        print("Run Acunetix Successfully")
            
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Recon Domain")
    parser.add_argument("-d", "--domain", required=True, help="Specify the domain")
    parser.add_argument("-o", "--output", help="Specify the path of the result folder")
    parser.add_argument("-a", "--acunetix", action="store_true", help="Scan with Acunetix")
    args = parser.parse_args()
    main(args)