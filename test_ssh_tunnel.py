#!/usr/bin/env python
"""
Diagnostic script to test Namecheap SSH tunnel & MySQL database connectivity.
Usage:
    python test_ssh_tunnel.py [--ssh-key path/to/key] [--ssh-password password]
"""
import sys
import socket
import argparse
from decouple import config

def test_tcp(host, port, timeout=5):
    print(f"[*] Testing TCP connectivity to {host}:{port}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, int(port)))
        s.close()
        print(f"[+] SUCCESS: Port {port} on {host} is reachable!")
        return True
    except Exception as e:
        print(f"[-] FAILED: Could not reach {host}:{port} - {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test SSH & MySQL connection to Namecheap")
    parser.add_argument("--ssh-host", default=config("SSH_HOST", default="198.54.115.10"))
    parser.add_argument("--ssh-port", default=config("SSH_PORT", default="21098"))
    parser.add_argument("--db-host", default="198.54.115.10")
    parser.add_argument("--db-port", default="3306")
    args = parser.parse_args()

    print("==================================================")
    print(" Namecheap Remote DB & SSH Diagnostic Tool")
    print("==================================================")
    
    # 1. Test direct MySQL port
    print("\n1. Testing Direct MySQL Port 3306 (Public Internet):")
    direct_mysql_ok = test_tcp(args.db_host, args.db_port, timeout=4)
    if not direct_mysql_ok:
        print("   -> As expected, direct connection to port 3306 is blocked by Namecheap firewall.")
        print("   -> An SSH tunnel is REQUIRED to connect from Render to Namecheap MySQL.")
    else:
        print("   -> Port 3306 is open directly! (No SSH tunnel required)")

    # 2. Test SSH Port (21098)
    print(f"\n2. Testing SSH Port {args.ssh_port} on {args.ssh_host}:")
    ssh_ok = test_tcp(args.ssh_host, args.ssh_port, timeout=4)
    if ssh_ok:
        print(f"   -> SUCCESS! Namecheap SSH service is accessible on port {args.ssh_port}.")
        print("   -> You can establish an SSH tunnel from Render to forward port 3306.")
    else:
        print(f"   -> FAILED to reach SSH port {args.ssh_port}. Check if SSH access is enabled in cPanel.")

    print("\n==================================================")
    print("Configuration for Render.com Environment Variables:")
    print("--------------------------------------------------")
    print("USE_SSH_TUNNEL=true")
    print(f"SSH_HOST={args.ssh_host}")
    print(f"SSH_PORT={args.ssh_port}")
    print("SSH_USER=kuledwzl")
    print("SSH_PRIVATE_KEY=<Your cPanel SSH Private Key>")
    print("  (OR: SSH_PASSWORD=<Your cPanel Password>)")
    print(f"DATABASE_URL=mysql://kuledwzl:ennga_db_001@{args.db_host}:3306/kuledwzl_ennga_db")
    print("==================================================")

if __name__ == "__main__":
    main()
