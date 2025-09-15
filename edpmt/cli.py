#!/usr/bin/env python3
"""
EDPMT Command Line Interface
Provides server and client modes with comprehensive command-line options
"""

import asyncio
import argparse
import json
import logging
import os
import sys
import random
from pathlib import Path
from typing import Optional

from .transparent import EDPMTransparent, EDPMClient, TransportType
from .utils import setup_logging, get_system_info, ensure_dependencies, ConfigManager

# Optional PortKeeper integration
try:
    from portkeeper import PortRegistry  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    PortRegistry = None  # type: ignore


def create_parser():
    """Create the main argument parser"""
    parser = argparse.ArgumentParser(
        prog='edpmt',
        description='EDPM Transparent - Simple, Secure, Universal Hardware Communication',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start server with TLS on port 8888
  edpmt server --tls --port 8888
  
  # Start server in development mode
  edpmt server --dev --port 8080
  
  # Connect to server and execute command
  edpmt client --execute set gpio '{"pin": 17, "value": 1}'
  
  # Interactive client mode
  edpmt client --url https://localhost:8888 --interactive
  
  # Show system information
  edpmt info
  
  # Reset configuration to defaults
  edpmt config --reset
        """
    )
    
    parser.add_argument(
        '--version', 
        action='version', 
        version='%(prog)s 1.0.0'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--config-dir',
        type=Path,
        help='Configuration directory (default: ~/.edpm)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Server command
    server_parser = subparsers.add_parser(
        'server',
        help='Start EDPM server',
        description='Start the EDPM hardware control server'
    )
    
    server_parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0)'
    )
    
    server_parser.add_argument(
        '--port', '-p',
        type=int,
        default=8888,
        help='Port to listen on (default: 8888)'
    )
    
    server_parser.add_argument(
        '--hardware-simulators',
        action='store_true',
        help='Use hardware simulators instead of real hardware'
    )
    
    server_parser.add_argument(
        '--tls',
        action='store_true',
        help='Enable TLS encryption'
    )
    
    server_parser.add_argument(
        '--no-tls',
        action='store_true',
        help='Disable TLS encryption'
    )
    
    server_parser.add_argument(
        '--dev',
        action='store_true',
        help='Development mode (auto TLS, debug logging)'
    )
    
    server_parser.add_argument(
        '--name',
        help='Server instance name'
    )
    
    server_parser.add_argument(
        '--transport',
        choices=['local', 'network', 'browser', 'auto'],
        default='auto',
        help='Transport type (default: auto)'
    )
    
    # Auto-port via PortKeeper (optional)
    server_parser.add_argument(
        '--auto-port',
        action='store_true',
        help='Automatically reserve a free port via PortKeeper (falls back to system-assigned port if PortKeeper is unavailable)'
    )
    server_parser.add_argument(
        '--preferred-port',
        type=int,
        help='Preferred port to try first when using --auto-port'
    )
    server_parser.add_argument(
        '--port-range',
        nargs=2,
        type=int,
        metavar=('START', 'END'),
        help='Port range [START, END] to search when using --auto-port'
    )
    server_parser.add_argument(
        '--write-env-key',
        metavar='KEY',
        help='If set with --auto-port, write KEY=PORT to a .env file'
    )
    server_parser.add_argument(
        '--env-path',
        default='.env',
        help='Path to .env file to write when using --auto-port (default: .env)'
    )
    
    # Client command
    client_parser = subparsers.add_parser(
        'client',
        help='Connect to EDPM server',
        description='Connect to an EDPM server and execute commands'
    )
    
    client_parser.add_argument(
        '--url',
        default='http://localhost:8888',
        help='Server URL (default: http://localhost:8888)'
    )
    
    client_parser.add_argument(
        '--execute',
        nargs=3,
        metavar=('ACTION', 'TARGET', 'PARAMS'),
        help='Execute single command: ACTION TARGET PARAMS_JSON'
    )
    
    client_parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Start interactive mode'
    )
    
    client_parser.add_argument(
        '--websocket',
        action='store_true',
        help='Use WebSocket connection'
    )
    
    # Info command
    info_parser = subparsers.add_parser(
        'info',
        help='Show system information',
        description='Display comprehensive system and hardware information'
    )
    
    info_parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format'
    )
    
    # Config command
    config_parser = subparsers.add_parser(
        'config',
        help='Manage configuration',
        description='View and modify EDPM configuration'
    )
    
    config_parser.add_argument(
        '--show',
        action='store_true',
        help='Show current configuration'
    )
    
    config_parser.add_argument(
        '--set',
        nargs=2,
        metavar=('KEY', 'VALUE'),
        help='Set configuration value: KEY VALUE'
    )
    
    config_parser.add_argument(
        '--get',
        metavar='KEY',
        help='Get configuration value'
    )
    
    config_parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset configuration to defaults'
    )
    
    # Test command
    test_parser = subparsers.add_parser(
        'test',
        help='Test hardware interfaces',
        description='Test various hardware interfaces and simulators'
    )
    
    test_parser.add_argument(
        '--gpio',
        action='store_true',
        help='Test GPIO interface'
    )
    
    test_parser.add_argument(
        '--i2c',
        action='store_true',
        help='Test I2C interface'
    )
    
    test_parser.add_argument(
        '--spi',
        action='store_true',
        help='Test SPI interface'
    )
    
    test_parser.add_argument(
        '--uart',
        action='store_true',
        help='Test UART interface'
    )
    
    test_parser.add_argument(
        '--all',
        action='store_true',
        help='Test all interfaces'
    )
    
    return parser


async def server_main(args):
    """Main function for server command"""
    print_header()
    
    if getattr(args, 'auto_port', False):
        reserved_port = None
        try:
            if PortRegistry is not None:
                reg = PortRegistry()
                # Defaults for EDPMT when not explicitly provided
                preferred = getattr(args, 'preferred_port', None)
                rng = tuple(args.port_range) if args.port_range else None
                if preferred is None:
                    preferred = 8888
                if rng is None:
                    rng = (8888, 8988)
                res = reg.reserve(preferred=preferred, port_range=rng, host=args.host, hold=False, owner='edpmt')
                reserved_port = res.port
                # Write SERVICE_PORT to .env by default (generic). Keep legacy EDPMT_PORT for compatibility.
                write_key = getattr(args, 'write_env_key', None) or 'SERVICE_PORT'
                env_path = getattr(args, 'env_path', '.env') or '.env'
                reg.write_env({write_key: str(res.port)}, path=env_path)
                if write_key == 'SERVICE_PORT':
                    # Also write legacy alias
                    reg.write_env({'EDPMT_PORT': str(res.port)}, path=env_path)
            else:
                raise ImportError('PortKeeper not installed')
        except Exception as e:
            print(f"⚠️ PortKeeper auto-port failed ({e}). Falling back to system-assigned port.")
        if reserved_port is None:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((args.host, 0))
            reserved_port = s.getsockname()[1]
            s.close()
        args.port = reserved_port
    
    config = {
        'dev_mode': args.dev,
        'host': args.host,
        'port': args.port,
        'tls': not args.no_tls,
        'hardware_simulators': args.hardware_simulators
    }
    server = EDPMTransparent(
        name=args.name if args.name else f"edpm_{random.randint(100000, 999999)}",
        config=config
    )
    
    print(f"""
🚀 Server Configuration:
   • Name: {server.name}
   • Transport: {server.transport_type.value}
   • Host: {args.host}
   • Port: {args.port}
   • TLS: {'✅ Enabled' if server.tls_enabled else '❌ Disabled'}
   • Development: {'✅ Yes' if args.dev else '❌ No'}
   • Hardware Simulators: {'✅ Yes' if args.hardware_simulators else '❌ No'}

🌐 Access Points:
   • Web Interface: {'https' if server.tls_enabled else 'http'}://{args.host}:{args.port}
   • REST API: {'https' if server.tls_enabled else 'http'}://{args.host}:{args.port}/api/execute
   • WebSocket: {'wss' if server.tls_enabled else 'ws'}://{args.host}:{args.port}/ws
   • Health Check: {'https' if server.tls_enabled else 'http'}://{args.host}:{args.port}/health
"""
    )
    
    print("Starting server... Press Ctrl+C to stop.")
    
    try:
        await server.start_server()
        # Keep the server running
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        print("Server shutdown requested")
        await server.shutdown()
        return 0
    except KeyboardInterrupt:
        print("Server stopped by user")
        await server.shutdown()
        return 0
    except Exception as e:
        print(f"❌ Server error: {e}")
        await server.shutdown()
        return 1


async def client_main(args):
    """Main function for client mode"""
    client = EDPMClient(url=args.url)
    
    try:
        if args.websocket:
            print(f"🔌 Connecting to WebSocket: {args.url}/ws")
            await client.connect_websocket()
            print("✅ WebSocket connected")
        
        if args.execute:
            # Single command execution
            action, target, params_str = args.execute
            params = json.loads(params_str) if params_str else {}
            
            print(f"📤 Executing: {action} {target} {json.dumps(params)}")
            
            result = await client.execute(action, target, **params)
            print(f"✅ Result: {json.dumps(result, indent=2)}")
            
        elif args.interactive:
            # Interactive mode
            print("""
🎮 EDPM Interactive Client
Commands: <action> <target> [params_json]
Special commands: 
  • help - Show this help
  • quit/exit - Exit client
  • status - Show connection status
  • examples - Show command examples

Examples:
  set gpio {"pin": 17, "value": 1}
  get gpio {"pin": 18}
  scan i2c
  play audio {"frequency": 440, "duration": 1.0}
""")
            
            while True:
                try:
                    line = input("edpmt> ").strip()
                    
                    if not line:
                        continue
                    
                    if line.lower() in ['quit', 'exit']:
                        break
                    elif line.lower() == 'help':
                        print_help()
                        continue
                    elif line.lower() == 'status':
                        await print_status(client)
                        continue
                    elif line.lower() == 'examples':
                        print_examples()
                        continue
                    
                    # Parse command
                    parts = line.split(None, 2)
                    if len(parts) < 2:
                        print("❌ Invalid command. Use: <action> <target> [params]")
                        continue
                    
                    action = parts[0]
                    target = parts[1]
                    params = json.loads(parts[2]) if len(parts) > 2 else {}
                    
                    result = await client.execute(action, target, **params)
                    print(f"✅ {json.dumps(result, indent=2)}")
                    
                except KeyboardInterrupt:
                    break
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON: {e}")
                except Exception as e:
                    print(f"❌ Error: {e}")
            
            print("👋 Goodbye!")
        
        else:
            # Default: show help
            print("❌ No action specified. Use --execute or --interactive")
            return 1
        
    except Exception as e:
        print(f"❌ Client error: {e}")
        return 1
    finally:
        await client.close()
    
    return 0


def info_main(args):
    """Main function for info command"""
    info = get_system_info()
    
    if args.json:
        print(json.dumps(info, indent=2))
    else:
        print("""
╔══════════════════════════════════════════════════════════════╗
║                    System Information                        ║
╚══════════════════════════════════════════════════════════════╝
""")
        
        print(f"🖥️  Platform: {info['platform']}")
        print(f"💻 System: {info['system']} ({info['machine']})")
        print(f"🐍 Python: {info['python_version']}")
        
        if 'hardware' in info:
            print(f"🔧 Hardware: {info['hardware']}")
        if 'revision' in info:
            print(f"📋 Revision: {info['revision']}")
        
        print(f"\n🔌 Available Interfaces:")
        print(f"   • GPIO Pins: {len(info['gpio_pins'])} pins")
        print(f"   • I2C Buses: {info['i2c_buses']}")
        print(f"   • SPI Buses: {info['spi_buses']}")
        print(f"   • UART Ports: {len(info['uart_ports'])} ports")
        
        if 'memory_total' in info:
            print(f"\n💾 Memory: {info['memory_total']} total")
            if 'memory_available' in info:
                print(f"          {info['memory_available']} available")
    
    return 0


def config_main(args):
    """Main function for config command"""
    config_manager = ConfigManager(args.config_dir)
    
    if args.show:
        print("📋 Current Configuration:")
        print(json.dumps(config_manager._config, indent=2))
    
    elif args.set:
        key, value = args.set
        # Try to parse as JSON, fall back to string
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            pass
        
        config_manager.set(key, value)
        print(f"✅ Set {key} = {json.dumps(value)}")
    
    elif args.get:
        value = config_manager.get(args.get)
        print(json.dumps(value, indent=2))
    
    elif args.reset:
        config_manager.reset_to_defaults()
        print("✅ Configuration reset to defaults")
    
    else:
        print("❌ No config action specified. Use --show, --set, --get, or --reset")
        return 1
    
    return 0


async def test_main(args):
    """Main function for test command"""
    from .hardware import (
        create_gpio_interface, create_i2c_interface,
        create_spi_interface, create_uart_interface
    )
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                     Hardware Interface Tests                ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    if args.gpio or args.all:
        print("\n🔌 Testing GPIO interface...")
        try:
            gpio = create_gpio_interface()
            async with gpio:
                # Test setting and reading a pin
                await gpio.set(17, 1)
                await asyncio.sleep(0.1)
                value = await gpio.get(17)
                print(f"   ✅ GPIO pin 17: {value} ({'simulator' if gpio.is_simulator else 'hardware'})")
        except Exception as e:
            print(f"   ❌ GPIO test failed: {e}")
    
    if args.i2c or args.all:
        print("\n🔄 Testing I2C interface...")
        try:
            i2c = create_i2c_interface()
            async with i2c:
                devices = await i2c.scan()
                print(f"   ✅ I2C devices found: {[hex(d) for d in devices]} ({'simulator' if i2c.is_simulator else 'hardware'})")
        except Exception as e:
            print(f"   ❌ I2C test failed: {e}")
    
    if args.spi or args.all:
        print("\n🔄 Testing SPI interface...")
        try:
            spi = create_spi_interface()
            async with spi:
                test_data = b'\x01\x02\x03'
                result = await spi.transfer(test_data)
                print(f"   ✅ SPI transfer: {test_data.hex()} -> {result.hex()} ({'simulator' if spi.is_simulator else 'hardware'})")
        except Exception as e:
            print(f"   ❌ SPI test failed: {e}")
    
    if args.uart or args.all:
        print("\n📡 Testing UART interface...")
        try:
            uart = create_uart_interface()
            async with uart:
                test_data = b'Hello UART!'
                await uart.write('/dev/ttyUSB0', test_data)
                result = await uart.read('/dev/ttyUSB0', len(test_data))
                print(f"   ✅ UART loopback: {test_data} -> {result} ({'simulator' if uart.is_simulator else 'hardware'})")
        except Exception as e:
            print(f"   ❌ UART test failed: {e}")
    
    print("\n✅ Hardware tests completed!")
    return 0


def print_help():
    """Print interactive help"""
    print("""
📖 EDPM Interactive Commands:

GPIO Commands:
  set gpio {"pin": 17, "value": 1}      - Set GPIO pin 17 to HIGH
  set gpio {"pin": 17, "value": 0}      - Set GPIO pin 17 to LOW  
  get gpio {"pin": 18}                  - Read GPIO pin 18
  pwm gpio {"pin": 18, "frequency": 1000, "duty_cycle": 50}

I2C Commands:
  scan i2c                              - Scan I2C bus for devices
  read i2c {"device": 118, "register": 208, "length": 1}
  write i2c {"device": 118, "register": 208, "data": [255]}

SPI Commands:
  transfer spi {"data": [1, 2, 3], "bus": 0, "device": 0}

UART Commands:
  write uart {"port": "/dev/ttyUSB0", "data": [72, 101, 108, 108, 111]}
  read uart {"port": "/dev/ttyUSB0", "length": 5}

Audio Commands:
  play audio {"frequency": 440, "duration": 1.0}
  play audio {"frequency": 880, "duration": 0.5}
""")


async def print_status(client):
    """Print client connection status"""
    try:
        # Test connection with health check
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{client.url}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ Connected to {client.url}")
                    print(f"   Server: {data.get('name', 'unknown')}")
                    print(f"   Transport: {data.get('transport', 'unknown')}")
                    print(f"   TLS: {'✅' if data.get('tls') else '❌'}")
                    print(f"   Uptime: {data.get('uptime', 0):.1f}s")
                else:
                    print(f"❌ Server responded with status {resp.status}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")


def print_examples():
    """Print command examples"""
    print("""
💡 Example Commands:

Basic GPIO:
  set gpio {"pin": 17, "value": 1}
  get gpio {"pin": 17}
  pwm gpio {"pin": 18, "frequency": 1000, "duty_cycle": 75}

I2C Sensor Reading:
  scan i2c
  read i2c {"device": 0x76, "register": 0xD0, "length": 1}    # BME280 ID
  read i2c {"device": 0x48, "register": 0x00, "length": 2}    # ADS1115 ADC

Audio Generation:
  play audio {"frequency": 262, "duration": 0.5}              # C note
  play audio {"frequency": 440, "duration": 1.0}              # A note
  play audio {"frequency": 880, "duration": 0.25}             # A octave

Quick Tests:
  set gpio {"pin": 17, "value": 1}; get gpio {"pin": 17}
""")


def print_header():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    EDPM Transparent Server                  ║
║                                                              ║
║  🔧 Simple • 🔒 Secure • 🌐 Universal                      ║
╚══════════════════════════════════════════════════════════════╝
""")


def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    log_level = 'DEBUG' if args.debug else ('INFO' if args.verbose else 'WARNING')
    setup_logging(log_level)
    
    # Ensure dependencies are available
    ensure_dependencies()
    
    # Handle commands
    if args.command == 'server':
        return asyncio.run(server_main(args))
    elif args.command == 'client':
        return asyncio.run(client_main(args))
    elif args.command == 'info':
        return info_main(args)
    elif args.command == 'config':
        return config_main(args)
    elif args.command == 'test':
        return asyncio.run(test_main(args))
    else:
        parser.print_help()
        return 1


# Entry points for setup.py console_scripts
def server_main_entry():
    """Entry point for edpmt-server command"""
    sys.argv = ['edpmt', 'server'] + sys.argv[1:]
    return main()


def client_main_entry():
    """Entry point for edpmt-client command"""  
    sys.argv = ['edpmt', 'client'] + sys.argv[1:]
    return main()


if __name__ == '__main__':
    sys.exit(main())
