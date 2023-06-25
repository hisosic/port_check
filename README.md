# Server Port Checker

This script retrieves a list of IP addresses using the `curl` command and checks the status of specific ports (7100 and 9000) for each IP address.

## Prerequisites

- Bash
- `curl` command-line tool
- `jq` command-line tool

## Usage

1. Make sure you have Bash, `curl`, and `jq` installed.

2. Run the script using the following command:

   ```bash
   bash server_port_checker.sh

The script will execute the curl command to retrieve a list of IP addresses.

It will then check the status of ports 7100 and 9000 for each IP address.

The script will display a table showing the IP address, status of port 7100, and status of port 9000 for each IP address.


## Example Output
```
IP Address                Port 7100      Port 9000     
------------------        ------------   ------------  
192.168.1.1               Open           Closed        
192.168.1.2               Closed         Open
```
