#!/usr/bin/env python3
"""
EDPMT Utilities
Helper functions for certificate generation, dependency management, and platform detection
"""

import os
import sys
import subprocess
import logging
import datetime
import ipaddress
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger('EDPM.Utils')


def ensure_dependencies():
    """Auto-install required packages if missing"""
    required_packages = [
        'cryptography',
        'aiohttp',
        'aiohttp-cors',
        'websockets'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.info(f"Installing missing packages: {missing_packages}")
        for package in missing_packages:
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", package
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.info(f"Successfully installed {package}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install {package}: {e}")
                raise ImportError(f"Required package '{package}' is not available and auto-install failed")


def generate_certificates(cert_file: Path, key_file: Path, 
                         common_name: str = "localhost",
                         valid_days: int = 365,
                         key_size: int = 2048):
    """Generate self-signed TLS certificates for HTTPS/WSS"""
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
    except ImportError:
        logger.error("cryptography package required for TLS certificate generation")
        raise ImportError("Install cryptography package: pip install cryptography")
    
    logger.info(f"Generating TLS certificates: {cert_file}, {key_file}")
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size
    )
    
    # Generate certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "EDPM Development"),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])
    
    # Create certificate builder
    cert_builder = x509.CertificateBuilder()
    cert_builder = cert_builder.subject_name(subject)
    cert_builder = cert_builder.issuer_name(issuer)
    cert_builder = cert_builder.public_key(private_key.public_key())
    cert_builder = cert_builder.serial_number(x509.random_serial_number())
    cert_builder = cert_builder.not_valid_before(datetime.datetime.utcnow())
    cert_builder = cert_builder.not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=valid_days)
    )
    
    # Add Subject Alternative Names
    san_list = [
        x509.DNSName("localhost"),
        x509.DNSName("127.0.0.1"),
        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        x509.IPAddress(ipaddress.IPv6Address("::1")),
    ]
    
    try:
        # Add local network interfaces
        import socket
        hostname = socket.gethostname()
        san_list.append(x509.DNSName(hostname))
        
        # Try to get local IP
        try:
            local_ip = socket.gethostbyname(hostname)
            san_list.append(x509.IPAddress(ipaddress.IPv4Address(local_ip)))
        except socket.gaierror:
            pass
            
    except ImportError:
        pass
    
    cert_builder = cert_builder.add_extension(
        x509.SubjectAlternativeName(san_list),
        critical=False,
    )
    
    # Add key usage extensions
    cert_builder = cert_builder.add_extension(
        x509.KeyUsage(
            key_encipherment=True,
            digital_signature=True,
            key_agreement=False,
            key_cert_sign=False,
            crl_sign=False,
            content_commitment=False,
            data_encipherment=False,
            encipher_only=False,
            decipher_only=False
        ),
        critical=True,
    )
    
    cert_builder = cert_builder.add_extension(
        x509.ExtendedKeyUsage([
            x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
            x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
        ]),
        critical=True,
    )
    
    # Sign certificate
    cert = cert_builder.sign(private_key, hashes.SHA256())
    
    # Write certificate to file
    with open(cert_file, 'wb') as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    # Write private key to file
    with open(key_file, 'wb') as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # Set restrictive permissions on key file
    os.chmod(key_file, 0o600)
    os.chmod(cert_file, 0o644)
    
    logger.info("TLS certificates generated successfully")
    logger.info(f"Certificate: {cert_file}")
    logger.info(f"Private key: {key_file}")


def detect_hardware_platform() -> str:
    """Detect the current hardware platform"""
    try:
        # Check for Raspberry Pi
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read().lower()
            if 'raspberry pi' in cpuinfo:
                return 'raspberry_pi'
            elif 'nvidia tegra' in cpuinfo:
                return 'nvidia_jetson'
            elif 'bcm' in cpuinfo and 'arm' in cpuinfo:
                return 'arm_sbc'  # Generic ARM single-board computer
    except (FileNotFoundError, PermissionError):
        pass
    
    # Check for Docker environment
    if os.path.exists('/.dockerenv'):
        return 'docker'
    
    # Check operating system
    import platform
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if system == 'linux':
        if 'arm' in machine:
            return 'linux_arm'
        else:
            return 'linux_x86'
    elif system == 'windows':
        return 'windows'
    elif system == 'darwin':
        return 'macos'
    
    return 'unknown'


def get_gpio_pins() -> List[int]:
    """Get available GPIO pins based on platform"""
    platform = detect_hardware_platform()
    
    if platform == 'raspberry_pi':
        # Raspberry Pi GPIO pins (BCM numbering)
        return [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
    else:
        # Generic pins for simulation
        return list(range(2, 28))


def get_i2c_buses() -> List[int]:
    """Get available I2C buses based on platform"""
    platform = detect_hardware_platform()
    
    if platform in ['raspberry_pi', 'linux_arm', 'linux_x86']:
        buses = []
        for i in range(10):  # Check for I2C buses 0-9
            if os.path.exists(f'/dev/i2c-{i}'):
                buses.append(i)
        return buses if buses else [1]  # Default to bus 1 if none found
    else:
        return [0, 1]  # Default buses for simulation


def get_spi_buses() -> List[tuple]:
    """Get available SPI buses as (bus, device) tuples"""
    platform = detect_hardware_platform()
    
    if platform in ['raspberry_pi', 'linux_arm', 'linux_x86']:
        buses = []
        for bus in range(2):  # Check SPI buses 0-1
            for device in range(2):  # Check devices 0-1
                if os.path.exists(f'/dev/spidev{bus}.{device}'):
                    buses.append((bus, device))
        return buses if buses else [(0, 0), (0, 1)]  # Default
    else:
        return [(0, 0), (0, 1), (1, 0), (1, 1)]  # Default for simulation


def get_uart_ports() -> List[str]:
    """Get available UART/serial ports"""
    platform = detect_hardware_platform()
    ports = []
    
    if platform == 'raspberry_pi':
        # Raspberry Pi serial ports
        possible_ports = [
            '/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2',
            '/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyACM2',
            '/dev/serial0', '/dev/serial1',
            '/dev/ttyAMA0', '/dev/ttyAMA1'
        ]
    elif platform.startswith('linux'):
        possible_ports = [
            '/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2', '/dev/ttyUSB3',
            '/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyACM2', '/dev/ttyACM3',
            '/dev/ttyS0', '/dev/ttyS1', '/dev/ttyS2', '/dev/ttyS3'
        ]
    elif platform == 'windows':
        possible_ports = [f'COM{i}' for i in range(1, 21)]  # COM1 to COM20
    else:
        # Generic/simulation ports
        possible_ports = ['/dev/ttyUSB0', 'COM1']
    
    # Check which ports actually exist
    for port in possible_ports:
        if platform == 'windows':
            # On Windows, we can't easily check existence without opening
            ports.append(port)
        else:
            if os.path.exists(port):
                ports.append(port)
    
    return ports if ports else ['/dev/ttyUSB0']  # At least one for simulation


def format_bytes(data: bytes, format_type: str = 'hex') -> str:
    """Format bytes for display"""
    if format_type == 'hex':
        return data.hex().upper()
    elif format_type == 'bin':
        return ' '.join(f'{b:08b}' for b in data)
    elif format_type == 'dec':
        return ' '.join(f'{b:03d}' for b in data)
    elif format_type == 'ascii':
        return ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data)
    else:
        return str(data)


def create_config_dir() -> Path:
    """Create EDPM configuration directory"""
    config_dir = Path.home() / '.edpm'
    config_dir.mkdir(exist_ok=True, parents=True)
    
    # Create subdirectories
    (config_dir / 'certs').mkdir(exist_ok=True)
    (config_dir / 'logs').mkdir(exist_ok=True)
    (config_dir / 'config').mkdir(exist_ok=True)
    
    return config_dir


def setup_logging(level: str = 'INFO', log_file: Optional[str] = None):
    """Setup logging configuration for EDPM"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # Setup file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('websockets').setLevel(logging.WARNING)


def get_system_info() -> dict:
    """Get comprehensive system information"""
    import platform
    
    info = {
        'platform': detect_hardware_platform(),
        'system': platform.system(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'gpio_pins': get_gpio_pins(),
        'i2c_buses': get_i2c_buses(),
        'spi_buses': get_spi_buses(),
        'uart_ports': get_uart_ports(),
    }
    
    # Add CPU info on Linux
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            # Extract useful info
            lines = cpuinfo.split('\n')
            for line in lines:
                if line.startswith('Hardware'):
                    info['hardware'] = line.split(':', 1)[1].strip()
                elif line.startswith('Revision'):
                    info['revision'] = line.split(':', 1)[1].strip()
                elif line.startswith('Serial'):
                    info['serial'] = line.split(':', 1)[1].strip()
    except (FileNotFoundError, PermissionError):
        pass
    
    # Add memory info
    try:
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
            lines = meminfo.split('\n')
            for line in lines:
                if line.startswith('MemTotal'):
                    info['memory_total'] = line.split(':', 1)[1].strip()
                elif line.startswith('MemAvailable'):
                    info['memory_available'] = line.split(':', 1)[1].strip()
    except (FileNotFoundError, PermissionError):
        pass
    
    return info


def validate_pin_number(pin: int, interface: str = 'gpio') -> bool:
    """Validate if a pin number is valid for the given interface"""
    if interface == 'gpio':
        valid_pins = get_gpio_pins()
        return pin in valid_pins
    elif interface == 'i2c':
        # I2C addresses are typically 7-bit (0x03 to 0x77)
        return 0x03 <= pin <= 0x77
    elif interface == 'spi':
        # SPI device numbers are typically 0-1
        return 0 <= pin <= 1
    
    return False


class ConfigManager:
    """Manage EDPM configuration files"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or create_config_dir()
        self.config_file = self.config_dir / 'config' / 'edpm.json'
        self._config = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                import json
                with open(self.config_file, 'r') as f:
                    self._config = json.load(f)
                logger.debug(f"Configuration loaded from {self.config_file}")
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                self._config = {}
        else:
            self._config = self._default_config()
            self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            import json
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
            logger.debug(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def _default_config(self) -> dict:
        """Default configuration"""
        return {
            'server': {
                'host': '0.0.0.0',
                'port': 8888,
                'tls': True,
                'auto_start': False,
            },
            'hardware': {
                'gpio_mode': 'BCM',
                'i2c_bus': 1,
                'spi_bus': 0,
                'uart_baudrate': 9600,
            },
            'logging': {
                'level': 'INFO',
                'file': None,
            },
            'development': {
                'use_simulators': False,
                'debug_mode': False,
            }
        }
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value):
        """Set configuration value"""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save_config()
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self._config = self._default_config()
        self.save_config()
