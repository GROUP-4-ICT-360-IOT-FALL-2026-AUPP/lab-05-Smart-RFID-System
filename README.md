# Lab 5: Smart RFID Attendance System with Cloud & SD Logging
 
## Plan
 
We build a simple RFID-based attendance system that identifies a student from their card, logs the attendance both locally and in the cloud, and gives instant audio feedback. It does not do any analytics or reporting, it only collects attendance records.
 
The components we use:
 
* ESP32 development board running MicroPython
* RFID-RC522 reader (SPI) to read the card UID
* MicroSD card module (SPI) to store attendance in a CSV file
* Buzzer for real-time feedback
* Wi-Fi + NTP to get the current date and time
* Google Firestore (REST API) to store attendance records remotely
Each valid scan is matched against a predefined student table, then saved to the SD card and sent to Firestore. Unknown cards are rejected and nothing is saved or sent.
 
## Wiring
 
> **Warning:** The RC522 is a 3.3V device. Applying 5V will burn it.
 
| RFID-RC522 | ESP32 |
|------------|-------|
| 3.3V       | 3.3V  |
| RST        | D22   |
| GND        | GND   |
| MISO       | D19   |
| MOSI       | D23   |
| SCK        | D18   |
| SDA (CS)   | D16   |
 
| SD Card Module | ESP32 |
|----------------|-------|
| CS             | D13   |
| SCK            | D14   |
| MOSI           | D15   |
| MISO           | D2    |
| VCC            | 5V    |
| GND            | GND   |
 
| Buzzer | ESP32 |
|--------|-------|
| -      | GND   |
| +      | 5V    |
| S      | D4    |
 
The RFID reader uses SPI bus 1 and the SD card uses a separate SPI bus 2, so the two modules do not conflict.
 
## How it works
 
1. On boot, the ESP32 connects to Wi-Fi and syncs its clock using NTP (UTC), then mounts the SD card.
2. If `/sd/attendance.csv` does not exist, it is created with a header row.
3. The main loop continuously polls the RC522 for a card and reads its UID as a hex string (e.g. `88041BBD`).
4. The UID is looked up in the `students` dictionary.
5. **Valid card:**
   * Generate the datetime as `YYYY-MM-DD HH:MM:SS` (UTC+7, Cambodia time)
   * Buzzer beeps for 0.3 seconds
   * Append a row to the SD card CSV
   * POST the record to Firestore
6. **Unknown card:**
   * Print `Unknown Card`
   * Buzzer sounds for 3 seconds
   * Nothing is saved or sent
7. Wait 1 second to avoid double-reads, then go back to scanning.
See `lab5.drawio.svg`  for the full logic.
  
## Data format
 
### CSV (SD card)
 
File: `/sd/attendance.csv`
 
```
UID,Name,StudentID,Major,DateTime
88041BBD,Alice,S001,Computer Science,2026-11-19 09:15:32
944C2007FF,Bob,S002,Electronics,2026-11-19 09:16:05
```
 
### Firestore
 
Collection: `attendance`. Each scan creates one document with these fields:
 
| Field        | Type   |
|--------------|--------|
| `uid`        | string |
| `name`       | string |
| `student_id` | string |
| `major`      | string |
| `datetime`   | string |
 
## Setup
 
### Flashing MicroPython
 
Download the ESP32 MicroPython firmware from [micropython.org](https://micropython.org/download/ESP32_GENERIC/), then:
 
```
esptool.py --port <PORT> erase_flash
esptool.py --port <PORT> --baud 460800 write_flash -z 0x1000 <firmware>.bin
```
 
Open Thonny, select **MicroPython (ESP32)** as the interpreter and pick your COM port.
 
### Libraries
 
Upload these to the ESP32 (they are not built in):
 
* `mfrc522.py` (RC522 driver)
* `sdcard.py` (SD card driver)
`network`, `ntptime`, `urequests`, `ujson` and `machine` are already included in MicroPython.
 
### Setting up Firestore
 
1. Create a project in the [Firebase console](https://console.firebase.google.com/) and add a **Firestore Database**.
2. Create a collection named `attendance`.
3. Set the Firestore rules to allow writes for the lab (test mode only, do not use in production).
4. Copy your **Project ID** and **Web API key** from the project settings.
### Configuring the code
 
Edit the top of `main.py`:
 
```python
WIFI_SSID = "<your wifi name>"
WIFI_PASSWORD = "<your wifi password>"
 
FIREBASE_PROJECT_ID = "<your project id>"
FIREBASE_API_KEY = "<your web api key>"
FIRESTORE_COLLECTION = "attendance"
 
TIMEZONE_OFFSET_HOURS = 7   # Cambodia = UTC+7
```
 
Add your cards to the student table (UID as uppercase hex, no spaces):
 
```python
students = {
    "88041BBD": {"name": "Alice", "student_id": "S001", "major": "Computer Science"},
    ...
}
```
 
To find a card's UID, scan it. Unknown cards print their UID in the Thonny shell.
 
### Format the SD card
 
Format the SD card as **FAT32** before using it.
 
## Usage
 
1. Wire everything as shown above and power the ESP32.
2. Save `main.py` to the ESP32 and run it (or let it start on boot).
3. Wait for `WiFi connected`, `Time synced` and `SD card ready` in the shell.
4. Tap a card on the reader:
   * Short beep (0.3 s): valid student, attendance saved
   * Long beep (3 s): unknown card, nothing saved
5. Check the CSV on the SD card and the `attendance` collection in Firestore.
## Troubleshooting
 
* **`SD card error`**: check wiring and that the card is FAT32. The module needs 5V on VCC.
* **`WiFi failed`**: the board still scans and saves to the SD card, but time will be wrong and Firestore posts will fail.
* **Wrong time**: NTP did not sync. Check Wi-Fi, then reboot.
* **Firestore response 403**: check the Firestore rules and API key.
* **Firestore response 404**: check the project ID and that the database exists.
* **Card not read**: confirm the RC522 is on 3.3V and the SPI pins match.
## Project files
 
| File                  | Description                              |
|-----------------------|------------------------------------------|
| `main.py`             | ESP32 MicroPython code                   |
| `lab5.drawio.svg`            | System flowchart                         |
| `attendance.csv`      | Sample attendance log from the SD card   |
| `firestore.jpg`       | Firestore screenshot                     |
| `demo.mp4`            | Demo video (60-90 sec)                   |
| `README.md`           | This file                                |
