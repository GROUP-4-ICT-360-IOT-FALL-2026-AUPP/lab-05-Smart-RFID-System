# RFID Student Attendance System

## Plan
We build an automated RFID student attendance tracking system using an ESP32 microcontroller.
The hardware components we will use include:
- RFID-RC522 reader (SPI) to scan and retrieve the unique ID (UID) from student RFID cards
- MicroSD card module (SPI) to log attendance records locally in CSV format[cite: 1]
- 3-pin active buzzer module to provide distinct audio feedback for valid and invalid scans[cite: 1]

The ESP32 connects to Wi-Fi, synchronizes its internal clock via NTP to generate accurate timestamps (`YYYY-MM-DD HH:MM:SS`), and compares scanned card UIDs against a predefined student database:
- **If UID is valid:** The buzzer sounds for `0.3` seconds, the record (`UID,Name,StudentID,Major,DateTime`) is appended to `attendance.csv` on the SD card, and the data is uploaded to Firebase Firestore via REST API.
- **If UID is invalid:** The buzzer sounds for `3` seconds, `"Unknown Card"` is displayed, and no data is saved or transmitted.

