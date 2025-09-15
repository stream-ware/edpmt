# EDPMT Docker Deployment

Kompletne rozwiązanie Docker do uruchomienia EDPMT na Raspberry Pi z pełną obsługą sprzętu i konteneryzacją.

## 🐳 Przegląd Architektury

### **Multi-Service Architecture**
- **EDPMT Server** - główny serwer EDPM w kontenerze
- **Frontend** - opcjonalny frontend GPIO w osobnym kontenerze
- **Volumes** - trwałe przechowywanie certyfikatów i logów
- **Networks** - izolowana sieć Docker dla bezpiecznej komunikacji

### **Hardware Integration**
- **GPIO Access** - pełny dostęp do pinów Raspberry Pi
- **I2C/SPI/UART** - mapowanie wszystkich interfejsów sprzętowych  
- **Device Mounting** - automatyczne wykrywanie i montowanie urządzeń
- **Privileged Mode** - dostęp do sprzętu na poziomie systemu

## 📦 Struktura Plików

```
examples/docker/
├── Dockerfile              # Obraz EDPMT
├── docker-compose.yml      # Orchestracja kontenerów
├── docker-entrypoint.sh    # Skrypt startowy
└── README.md              # Ta dokumentacja
```

## 🚀 Szybki Start

### **1. Przygotowanie Systemu**

```bash
# Aktualizuj system Raspberry Pi
sudo apt update && sudo apt upgrade -y

# Instaluj Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Instaluj Docker Compose
sudo apt install docker-compose -y

# Restartuj aby zastosować uprawnienia
sudo reboot
```

### **2. Uruchomienie przez Makefile**

```bash
# Z głównego katalogu EDPMT
make init-docker    # Inicjalizacja Docker
make build          # Budowanie obrazów
make start          # Start kontenerów
```

### **3. Ręczne Uruchomienie**

```bash
# Przejdź do katalogu Docker
cd examples/docker

# Zbuduj i uruchom
docker-compose up --build -d

# Sprawdź status
docker-compose ps
```

### **4. Dostęp do Usług**

Po uruchomieniu dostępne będą:

- **EDPMT Server**: `https://localhost:8888`
- **GPIO Frontend**: `http://localhost:5000` (jeśli włączony)
- **Web UI**: `https://localhost:8888/` (interfejs EDPMT)
- **WebSocket**: `wss://localhost:8888/ws`

## ⚙️ Konfiguracja

### **docker-compose.yml**

```yaml
version: '3.8'

services:
  edpmt-server:
    build: .
    container_name: edpmt-server
    ports:
      - "8888:8888"
    privileged: true  # Dostęp do sprzętu
    devices:
      - "/dev/i2c-1:/dev/i2c-1"      # I2C
      - "/dev/spidev0.0:/dev/spidev0.0"  # SPI
      - "/dev/ttyS0:/dev/ttyS0"      # UART
    volumes:
      - /sys:/sys                    # GPIO sysfs
      - ./certs:/app/certs           # Certyfikaty TLS
      - ./logs:/app/logs             # Logi
    environment:
      - EDPMT_PORT=8888
      - EDPMT_HOST=0.0.0.0
      - EDPMT_TLS=true
      - EDPMT_DEV_MODE=false
    restart: unless-stopped
    
  gpio-frontend:
    build:
      context: ../gpio-frontend
      dockerfile: Dockerfile
    container_name: gpio-frontend
    ports:
      - "5000:5000"
    depends_on:
      - edpmt-server
    environment:
      - EDPMT_URL=https://edpmt-server:8888
    restart: unless-stopped
```

### **Dockerfile**

```dockerfile
FROM python:3.9-slim

# Instaluj zależności systemowe
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    i2c-tools \
    && rm -rf /var/lib/apt/lists/*

# Utwórz użytkownika aplikacji
RUN useradd -m -s /bin/bash edpmt

# Kopiuj kod
WORKDIR /app
COPY . .

# Instaluj zależności Python
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir .

# Ustaw uprawnienia
RUN chown -R edpmt:edpmt /app
USER edpmt

# Port i skrypt startowy
EXPOSE 8888
ENTRYPOINT ["./docker-entrypoint.sh"]
```

### **docker-entrypoint.sh**

```bash
#!/bin/bash

# Sprawdź sprzęt
echo "🔍 Checking hardware availability..."

# GPIO
if [ -d "/sys/class/gpio" ]; then
    echo "✅ GPIO available"
    export EDPMT_GPIO_ENABLED=true
else
    echo "❌ GPIO not available - using simulator"
    export EDPMT_GPIO_ENABLED=false
fi

# I2C  
if [ -e "/dev/i2c-1" ]; then
    echo "✅ I2C available"
    export EDPMT_I2C_ENABLED=true
else
    echo "❌ I2C not available - using simulator"
    export EDPMT_I2C_ENABLED=false
fi

# SPI
if [ -e "/dev/spidev0.0" ]; then
    echo "✅ SPI available"
    export EDPMT_SPI_ENABLED=true
else
    echo "❌ SPI not available - using simulator"
    export EDPMT_SPI_ENABLED=false
fi

# UART
if [ -e "/dev/ttyS0" ]; then
    echo "✅ UART available"
    export EDPMT_UART_ENABLED=true
else
    echo "❌ UART not available - using simulator"
    export EDPMT_UART_ENABLED=false
fi

# Generuj certyfikaty TLS jeśli nie istnieją
if [ ! -f "/app/certs/server.crt" ]; then
    echo "🔐 Generating TLS certificates..."
    mkdir -p /app/certs
    python -c "
import sys
sys.path.append('/app')
from edpmt.utils import generate_self_signed_cert
generate_self_signed_cert('/app/certs')
"
fi

# Uruchom EDPMT server
echo "🚀 Starting EDPMT server..."
exec python -m edpmt server \
    --host ${EDPMT_HOST:-0.0.0.0} \
    --port ${EDPMT_PORT:-8888} \
    --tls-cert /app/certs/server.crt \
    --tls-key /app/certs/server.key \
    ${EDPMT_DEV_MODE:+--dev}
```

## 🔧 Zarządzanie Kontenerami

### **Podstawowe Operacje**

```bash
# Uruchomienie
docker-compose up -d

# Zatrzymanie
docker-compose down

# Restart
docker-compose restart

# Status
docker-compose ps

# Logi
docker-compose logs -f edpmt-server
```

### **Budowanie i Aktualizacje**

```bash
# Przebuduj obrazy
docker-compose build --no-cache

# Wymuś odświeżenie
docker-compose pull
docker-compose up --force-recreate
```

### **Czyszczenie**

```bash
# Usuń kontenery i wolumeny
docker-compose down -v

# Wyczyść obrazy
docker system prune -a
```

## 📊 Monitoring i Logi

### **Sprawdzanie Logów**

```bash
# Wszystkie logi
docker-compose logs

# Tylko EDPMT server
docker-compose logs edpmt-server

# Na żywo
docker-compose logs -f

# Ostatnie 100 linii
docker-compose logs --tail=100
```

### **Health Checks**

```bash
# Status kontenerów
docker-compose ps

# Health check EDPMT
curl -k https://localhost:8888/health

# Test połączenia
docker-compose exec edpmt-server python -c "
from edpmt import EDPMClient
import asyncio
async def test():
    client = EDPMClient('https://localhost:8888')
    info = await client.execute('info', 'system')
    print(f'EDPMT Server: {info}')
    await client.close()
asyncio.run(test())
"
```

### **System Metrics**

```bash
# Użycie zasobów
docker stats

# Szczegóły kontenerów
docker-compose top

# Zużycie dysku
docker system df
```

## 🔒 Bezpieczeństwo

### **TLS/SSL Configuration**
- **Self-signed certificates** generowane automatycznie
- **Persistent storage** w wolumenie `/app/certs`
- **HTTPS** wymuszony dla wszystkich połączeń
- **WSS** dla WebSocket connections

### **Container Security**
- **Non-root user** w kontenerze (edpmt)
- **Minimal attack surface** - tylko niezbędne pakiety
- **Isolated network** Docker dla komunikacji między kontenerami
- **Read-only filesystem** gdzie to możliwe

### **Hardware Access Control**
- **Privileged mode** tylko gdzie konieczny
- **Device mapping** ograniczony do potrzebnych urządzeń
- **Volume mounts** z określonymi uprawnieniami

## 🐛 Rozwiązywanie Problemów

### **Container nie startuje**

```bash
# Sprawdź logi błędów
docker-compose logs edpmt-server

# Sprawdź czy porty są wolne
netstat -tlnp | grep 8888

# Sprawdź uprawnienia urządzeń
ls -la /dev/i2c-* /dev/spi* /dev/tty*

# Test sprzętu
docker-compose exec edpmt-server ls -la /dev/
```

### **Brak dostępu do GPIO**

```bash
# Sprawdź czy GPIO są dostępne
ls -la /sys/class/gpio/

# Sprawdź uprawnienia użytkownika
groups $USER

# Dodaj do grupy gpio
sudo usermod -a -G gpio $USER
```

### **Problemy z I2C**

```bash
# Włącz I2C w raspi-config
sudo raspi-config
# Interface Options -> I2C -> Enable

# Sprawdź czy urządzenia są widoczne
i2cdetect -y 1

# Test w kontenerze
docker-compose exec edpmt-server i2cdetect -y 1
```

### **Problemy z SPI**

```bash
# Włącz SPI w raspi-config
sudo raspi-config
# Interface Options -> SPI -> Enable

# Sprawdź urządzenia SPI
ls -la /dev/spi*

# Test w kontenerze
docker-compose exec edpmt-server ls -la /dev/spi*
```

### **Port Already In Use**

```bash
# Znajdź proces używający portu
sudo lsof -i :8888

# Zatrzymaj konfliktujący kontener
docker ps | grep 8888
docker stop <container_id>
```

## ⚡ Optymalizacja

### **Performance Tuning**

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  edpmt-server:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
        reservations:
          memory: 256M
          cpus: '0.5'
```

### **Persistent Data**

```yaml
# Dodaj wolumeny dla danych
volumes:
  - ./data:/app/data          # Dane aplikacji
  - ./config:/app/config      # Konfiguracja
  - ./backups:/app/backups    # Kopie zapasowe
```

### **Multi-Architecture**

```dockerfile
# Support for ARM64 and AMD64
FROM --platform=${BUILDPLATFORM} python:3.9-slim

ARG TARGETPLATFORM
ARG BUILDPLATFORM

RUN echo "Building for ${TARGETPLATFORM} on ${BUILDPLATFORM}"
```

## 🔄 CI/CD Integration

### **GitHub Actions**

```yaml
# .github/workflows/docker.yml
name: Docker Build

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Build Docker image
      run: |
        cd examples/docker
        docker build -t edpmt:latest .
```

### **Automated Deployment**

```bash
#!/bin/bash
# deploy.sh - Automated deployment script

cd examples/docker

# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Health check
sleep 10
curl -k https://localhost:8888/health
```

---

**💡 Docker deployment zapewnia niezawodne, skalowalne i bezpieczne uruchomienie EDPMT na Raspberry Pi z pełną obsługą sprzętu!**
