- dodaj testy e2e z bash curl w ./ i python w tests/ 
- dodaj przykladowy frontend, gdzie mozna zobaczyc kontrole sprzetu np wizualizacji GPIO z RPI z mozliwoscia ustawienia WE/WY cyfrowych ora sczytywaniem i pokazywanie na frotnend aktualnych zmian (za pomoca przerwan) tych zmian na wejsciach gpio 
- stworz dokumentacje i w folderze example rowniez dla kazdego przykladu w folderze z przykladami w plikach examples/*/README.md

Zaimplementuj obsluge dynamiczna portow
✅ Plik 
.env
 - utworzony z konfiguracją domyślnych portów i zarządzania portami
✅ Automatyczne ładowanie 
.env
 - system szuka pliku w różnych lokalizacjach
✅ Wykrywanie zajętych portów - funkcja 
is_port_available()
 sprawdza dostępność
✅ Automatyczna inkrementacja - 
find_available_port()
 szuka wolnego portu w zakresie
🔧 Port 8080 był zajęty → System automatycznie wykrył konflikt
🚀 Przełączył na port 8082 → Znalazł pierwszy dostępny port w zakresie
✅ Serwer działa prawidłowo → Health check potwierdza działanie:

Co zostanie osiągnięte:
🔧 Plik 
.env
 z automatycznym zarządzaniem portami
✅ Utworzony 
.env
 z konfiguracją portów (8081 domyślnie, zakres 8080-8090)
✅ Automatyczne ładowanie - system szuka 
.env
 w różnych lokalizacjach
✅ Zarządzanie konfliktami - gdy port zajęty, automatycznie inkrementuje
🚀 System automatycznego wykrywania portów
✅ Sprawdzanie dostępności - funkcja 
is_port_available()
 testuje porty
✅ Automatyczna inkrementacja - 
find_available_port()
 szuka wolnego portu
✅ Zakres portów - konfigurowalny przez EDPM_PORT_RANGE_START/END



- dodaj kolejny przyklad z edycja komend poprzez scratch podobne rozwiazanie jak blockly, aby mozliwe bylo eydotawnaie wysylania i odbieranie danych komunikacji edpmt za pomoca budowanych z "klockow" wizualnych elementow, menu, widokow, ze zdefiniowanych templates
- stworz przyklady edycji i projektow wykorzystania scratch-poodbnych rozwizan

uzyj biblioteki python portkeeper w aktualnym projekcie /home/tom/github/stream-ware/edpmt w celu latwego przydzielania przy starcie dynamicznie portow i hostow w .env dla backendu i z udsotepnianiem tych zmiennych dla frontendu w config.json



chcialbym aby framework byl niezalezny od sprzetu,
aby komendy typy set_gpio, get_gpio byly niezalezne od EDPM 
i sprzęt był ustawiany i implementowany przy inicjacji edmp.
Aktualnie gpio jest częścią EDPM a powinna byc mozliwosc dodania dowolnego sprzetu i kontroli akcji i logow za pomocą prostej konfiguracji jako setup przed uzyciem EDPM, warstwa sprzetowa jest niezalezna, EDPM ma za zadanie obslugiwac komunikacje pomiedzy wszystkimi mozliwymi peryferiami. Po przygotowaniu takiej nowej wersji light, pokaż użycie w projekcie z GPIO, USB, i protokołem I2c oraz I2S

