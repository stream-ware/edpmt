# EDPMT GPIO Frontend - Interaktywna Wizualizacja GPIO

Nowoczesny frontend webowy do kontroli i monitorowania GPIO Raspberry Pi w czasie rzeczywistym z obsługą przerwań i WebSocket.

## 🌟 Funkcje

### **🎮 Interaktywna Kontrola GPIO**
- **Wizualizacja wszystkich pinów GPIO** Raspberry Pi (GPIO 2-27)
- **Kontrola trybu pinów** (IN/OUT) z obsługą pull-up/pull-down
- **Cyfrowe WE/WY** - ustawianie HIGH/LOW dla pinów wyjściowych
- **Odczytywanie pinów wejściowych** w czasie rzeczywistym
- **Kontrola PWM** z regulacją częstotliwości i wypełnienia

### **🔔 System Przerwań**
- **Monitorowanie przerwań** na pinach wejściowych
- **Powiadomienia w czasie rzeczywistym** o zmianach stanu
- **Licznik zmian** dla każdego pinu
- **Wizualne wyróżnienie** pinów z przerwaniami

### **📡 Komunikacja Real-time**
- **WebSocket** połączenie dla natychmiastowych aktualizacji
- **Automatyczne odświeżanie** stanu pinów
- **Synchronizacja** pomiędzy wieloma klientami
- **Log aktywności** w czasie rzeczywistym

### **🎨 Nowoczesny Interface**
- **Responsive design** działający na PC, tablet i telefon
- **Kolorowe wskaźniki** stanu pinów (HIGH/LOW)
- **Animacje i efekty wizualne** dla lepszego UX
- **Status połączenia** i monitoring w czasie rzeczywistym

## 📦 Wymagania

- **EDPMT Server** uruchomiony i dostępny
- **Python 3.8+**
- **Flask** i **Flask-SocketIO**
- **Raspberry Pi** (opcjonalnie - może działać z symulatorami)

```bash
# Instalacja zależności
pip install flask flask-socketio
```

## 🚀 Szybki Start

### **1. Uruchom EDPMT Server**

```bash
# W terminalu 1 - uruchom EDPMT server
edpmt server --dev --port 8888

# Lub przez Makefile
make server-dev
```

### **2. Uruchom GPIO Frontend**

```bash
# W terminalu 2 - uruchom GPIO frontend
cd examples/gpio-frontend
python app.py

# Lub przez Makefile (z głównego katalogu)
make frontend-demo
```

### **3. Otwórz Przeglądarkę**

Przejdź do: **http://localhost:5000**

## 🎛️ Używanie Dashboard

### **Panel Sterowania**
- **🔄 Refresh All** - odśwież stan wszystkich pinów
- **📊 Toggle Monitoring** - włącz/wyłącz monitoring przerwań
- **📖 Read All Inputs** - odczytaj wszystkie piny wejściowe
- **🛑 Emergency Stop** - ustaw wszystkie wyjścia na LOW

### **Kontrola Pinów**
Każdy pin GPIO ma swój panel z opcjami:

**Tryb Pin:**
- **IN** - pin wejściowy (odczyt)
- **OUT** - pin wyjściowy (zapis)

**Kontrola Wartości:**
- **HIGH** - ustaw pin na stan wysoki (3.3V)
- **LOW** - ustaw pin na stan niski (0V)
- **Read Value** - odczytaj aktualny stan pinu

**PWM (dla pinów PWM):**
- **Frequency** - częstotliwość w Hz
- **Duty Cycle** - wypełnienie 0-100%

**Przerwania (dla pinów wejściowych):**
- **Toggle** - włącz/wyłącz monitorowanie przerwań
- **Counter** - licznik zmian stanu

## 🔧 Konfiguracja

### **Parametry Startowe**

```bash
python app.py --help

# Opcje:
--host 0.0.0.0          # Adres bind (domyślnie 0.0.0.0)
--port 5000             # Port serwera (domyślnie 5000)  
--edpmt-url https://localhost:8888  # URL serwera EDPMT
--debug                 # Tryb debug
```

### **Przykład Uruchomienia**

```bash
# Uruchom na porcie 8080 z debug
python app.py --port 8080 --debug

# Połącz z zewnętrznym serwerem EDPMT
python app.py --edpmt-url https://rpi.local:8888
```

## 📊 Mapowanie Pinów GPIO Raspberry Pi

Frontend automatycznie rozpoznaje i konfiguruje piny według funkcji:

| Pin | Funkcja | Typ | Opis |
|-----|---------|-----|------|
| GPIO2 | SDA | I2C | I2C Data |
| GPIO3 | SCL | I2C | I2C Clock |
| GPIO4 | - | GPIO | GPIO ogólnego użytku |
| GPIO7,8 | CE1,CE0 | SPI | SPI Chip Enable |
| GPIO9,10,11 | MISO,MOSI,SCLK | SPI | SPI Communication |
| GPIO12,13 | PWM0,PWM1 | PWM | Hardware PWM |
| GPIO14,15 | TXD,RXD | UART | Serial Communication |
| GPIO17-27 | - | GPIO | GPIO ogólnego użytku |

## 🔔 System Przerwań

### **Włączanie Przerwań**
1. Ustaw pin w tryb **IN** (input)
2. Kliknij przełącznik **Interrupts** na ON
3. Zmiany stanu będą automatycznie wykrywane

### **Monitorowanie**
- **Przerwania** są sprawdzane co 100ms
- **Powiadomienia** pojawiają się natychmiastowo w interfejsie
- **Log aktywności** zapisuje wszystkie zmiany z timestamp
- **Wizualne efekty** wyróżniają piny z przerwaniami

## 📱 Responsive Design

### **Desktop (>1200px)**
- **Siatka 3-4 kolumn** pinów GPIO
- **Pełne etykiety** i opisy
- **Wszystkie kontrolki** widoczne

### **Tablet (768-1200px)**  
- **Siatka 2 kolumny** pinów
- **Kompaktowe kontrolki**
- **Zachowane funkcjonalności**

### **Mobile (<768px)**
- **Jedna kolumna** pinów
- **Uproszczony interface**
- **Touch-friendly** przyciski

## 🛠️ Rozwój i Debugowanie

### **Logi**
Logi są zapisywane w `logs/gpio-frontend.log`:

```bash
# Monitorowanie logów
tail -f logs/gpio-frontend.log

# Lub przez Makefile
make monitor-frontend
```

### **Debug Mode**
```bash
# Uruchom z debugowaniem
python app.py --debug

# Więcej szczegółowych logów
export FLASK_ENV=development
python app.py
```

### **Testowanie**
```bash
# Test połączenia z frontend
curl http://localhost:5000/health

# Lub przez Makefile
make test-frontend
```

## ⚡ Wydajność

### **Optymalizacje**
- **WebSocket** dla minimalizacji latencji
- **Monitoring przerwań** w osobnym wątku
- **Buforowanie stanu** pinów
- **Throttling** aktualizacji (100ms)

### **Limity**
- **50 wpisów** w logu aktywności
- **100ms** opóźnienie monitoringu
- **30s timeout** połączenia EDPMT

## 🐛 Rozwiązywanie Problemów

### **Frontend nie startuje**
```bash
# Sprawdź zależności
pip install flask flask-socketio

# Sprawdź port
netstat -tlnp | grep :5000
```

### **Brak połączenia z EDPMT**
```bash
# Sprawdź czy EDPMT działa
curl -k https://localhost:8888/health

# Sprawdź logi
tail -f logs/gpio-frontend.log
```

### **Przerwania nie działają**
1. Sprawdź czy pin jest w trybie **IN**
2. Włącz **monitoring** w głównym panelu
3. Sprawdź logi na błędy połączenia

## 📄 API Endpoints

### **HTTP REST API**
- `GET /` - Dashboard HTML
- `GET /health` - Status health check
- `GET /api/gpio/pins` - Stan wszystkich pinów
- `GET /api/gpio/pin/<pin>` - Stan pojedynczego pinu
- `POST /api/gpio/pin/<pin>` - Kontrola pinu
- `POST /api/gpio/monitor` - Toggle monitoringu

### **WebSocket Events**
- `connect/disconnect` - Połączenie klienta
- `gpio_pins` - Wysłanie stanu pinów
- `gpio_update` - Aktualizacja pinu
- `gpio_interrupt` - Powiadomienie o przerwaniu
- `gpio_control` - Kontrola przez WebSocket

## 🔒 Bezpieczeństwo

- **Lokalne połączenia** domyślnie (0.0.0.0)
- **HTTPS** dla połączeń z EDPMT
- **Walidacja** parametrów GPIO
- **Emergency Stop** dla bezpieczeństwa

---

**💡 Ten frontend zapewnia kompletną kontrolę GPIO Raspberry Pi przez przeglądarkę z monitorowaniem w czasie rzeczywistym i obsługą przerwań!**
