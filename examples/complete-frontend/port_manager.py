#!/usr/bin/env python3
"""
EDPMT Port Manager - Dynamic Port Allocation with Portkeeper
Systematically allocates ports and updates .env file for the frontend.
"""

import sys
import os
from pathlib import Path
from typing import Dict, Optional
import argparse

try:
    from portkeeper import PortRegistry
    from dotenv import load_dotenv, set_key
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Run: pip install --user --break-system-packages portkeeper python-dotenv")
    sys.exit(1)


class EDPMTPortManager:
    """Manages dynamic port allocation for EDPMT frontend using portkeeper."""
    
    def __init__(self, env_file: str = ".env"):
        self.env_file = Path(env_file)
        self.registry = PortRegistry()
        self.reservations = {}
        
        # Load existing environment
        if self.env_file.exists():
            load_dotenv(self.env_file)
    
    def allocate_ports(self, profiles: Dict[str, str]) -> Dict[str, int]:
        """
        Allocate ports for given profiles and update .env file.
        
        Args:
            profiles: Dict mapping profile names to env variable names
                     e.g. {"http": "HTTP_PORT", "ws": "WEBSOCKET_PORT"}
        
        Returns:
            Dict mapping profile names to allocated port numbers
        """
        allocated_ports = {}
        
        print("🔍 Allocating ports with portkeeper...")
        
        for profile_name, env_var in profiles.items():
            try:
                # Try to get preferred port from .env if exists
                preferred_port = None
                current_value = os.getenv(env_var)
                if current_value and current_value.isdigit():
                    preferred_port = int(current_value)
                
                # Reserve port using portkeeper
                reservation = self.registry.reserve(
                    preferred=preferred_port,
                    owner=f"edpmt-frontend-{profile_name}",
                    hold=True
                )
                
                allocated_port = reservation.port
                allocated_ports[profile_name] = allocated_port
                self.reservations[profile_name] = reservation
                
                # Update .env file
                set_key(self.env_file, env_var, str(allocated_port))
                
                print(f"✅ {profile_name}: {allocated_port} (env: {env_var})")
                
            except Exception as e:
                print(f"❌ Failed to allocate port for {profile_name}: {e}")
                sys.exit(1)
        
        return allocated_ports
    
    def get_port(self, profile: str) -> Optional[int]:
        """Get currently allocated port for a profile from .env file."""
        load_dotenv(self.env_file) # Ensure we have the latest values
        env_var_map = {
            "http": "HTTP_PORT",
            "websocket": "WEBSOCKET_PORT"
        }
        env_var = env_var_map.get(profile)
        if env_var:
            port_str = os.getenv(env_var)
            if port_str and port_str.isdigit():
                return int(port_str)
        return None
    
    def release_all(self):
        """Release all port reservations."""
        print("🔄 Releasing all port reservations...")
        for profile_name, reservation in self.reservations.items():
            try:
                self.registry.release(reservation)
                print(f"✅ Released port {reservation.port} for {profile_name}")
            except Exception as e:
                print(f"⚠️ Error releasing {profile_name}: {e}")
        
        self.reservations.clear()
    
    def status(self) -> Dict[str, int]:
        """Get status of all current port allocations."""
        status = {}
        for profile_name, reservation in self.reservations.items():
            status[profile_name] = reservation.port
        return status


def main():
    """CLI interface for port management."""
    parser = argparse.ArgumentParser(description="EDPMT Port Manager")
    parser.add_argument("command", choices=["allocate", "release", "status", "get"],
                       help="Command to execute")
    parser.add_argument("--profile", help="Profile name for 'get' command")
    parser.add_argument("--env-file", default=".env", help="Environment file path")
    
    args = parser.parse_args()
    
    manager = EDPMTPortManager(args.env_file)
    
    if args.command == "allocate":
        # Standard EDPMT frontend profiles
        profiles = {
            "http": "HTTP_PORT",
            "websocket": "WEBSOCKET_PORT"
        }
        
        ports = manager.allocate_ports(profiles)
        print(f"\n🎯 Allocated ports: HTTP={ports['http']}, WebSocket={ports['websocket']}")
        
        # Output for Makefile usage
        print(f"HTTP_PORT={ports['http']}")
        print(f"WEBSOCKET_PORT={ports['websocket']}")
        
    elif args.command == "get":
        if not args.profile:
            print("❌ --profile required for 'get' command", file=sys.stderr)
            sys.exit(1)

        port = manager.get_port(args.profile)
        if port:
            print(port)
        else:
            # Try to allocate if not found
            print(f"ℹ️ No port allocated for profile: {args.profile}. Checking .env...", file=sys.stderr)
            env_port = os.getenv(f"{args.profile.upper()}_PORT")
            if env_port and env_port.isdigit():
                print(env_port)
            else:
                print(f"❌ Cannot determine port for profile: {args.profile}", file=sys.stderr)
                sys.exit(1)
    
    elif args.command == "release":
        manager.release_all()
        print("✅ All ports released")
    
    elif args.command == "status":
        status = manager.status()
        if status:
            print("📊 Current port allocations:")
            for profile, port in status.items():
                print(f"  {profile}: {port}")
        else:
            print("ℹ️ No ports currently allocated")


if __name__ == "__main__":
    main()
