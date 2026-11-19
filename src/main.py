from machine import Pin, SPI
from mfrc522 import MFRC522
import time
import os
import network
import ntptime
import urequests
import ujson
import sdcard

WIFI_SSID = "Robotic WIFI"
WIFI_PASSWORD = "rbtWIFI@2025"

FIREBASE_PROJECT_ID = "lab5-15fbb"
FIREBASE_API_KEY = "AIzaSyAgXTOM84bNESkT3CQ9tPnZuxolXDzitJc"
FIRESTORE_COLLECTION = "attendance"

TIMEZONE_OFFSET_HOURS = 7          # Cambodia = UTC+7
CSV_PATH = "/sd/attendance.csv"

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        timeout = 15
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
    if wlan.isconnected():
        print("WiFi connected:", wlan.ifconfig()[0])
        return True
    print("WiFi failed")
    return False

students = {
    "88041BBD": {"name": "Alice",   "student_id": "S001", "major": "Computer Science"},
    "944C2007FF": {"name": "Bob",     "student_id": "S002", "major": "Electronics"},
    "A1B2C3D4": {"name": "Charlie", "student_id": "S003", "major": "Mechatronics"},
    "2913690655": {"name": "Charlie", "student_id": "S003", "major": "Mechatronics"},
    
}


spi = SPI(1, baudrate=1000000, polarity=0, phase=0,
          sck=Pin(18), mosi=Pin(23), miso=Pin(19))

rdr = MFRC522(spi=spi, gpioRst=Pin(22), gpioCs=Pin(16))


print("Scan RFID...")

buzzer = Pin(4, Pin.OUT)
buzzer.value(0)

# SD card (separate SPI bus 2, different pins from the RFID reader)
sd_spi = SPI(2, baudrate=1000000, polarity=0, phase=0,
             sck=Pin(14), mosi=Pin(15), miso=Pin(2))
sd_cs = Pin(13, Pin.OUT)


def beep(seconds):
    buzzer.value(1)
    time.sleep(seconds)
    buzzer.value(0)

def sync_time():
    try:
        ntptime.settime()  # sets the RTC to UTC
        print("Time synced")
    except Exception as e:
        print("NTP sync failed:", e)


def get_datetime():
    t = time.localtime(time.time() + TIMEZONE_OFFSET_HOURS * 3600)
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        t[0], t[1], t[2], t[3], t[4], t[5])


# ---------------- SD CARD ----------------
sd_ok = False


def mount_sd():
    global sd_ok
    try:
        sd = sdcard.SDCard(sd_spi, sd_cs)
        os.mount(os.VfsFat(sd), "/sd")
        # Create CSV with header if it doesn't exist yet
        try:
            os.stat(CSV_PATH)
        except OSError:
            with open(CSV_PATH, "w") as f:
                f.write("UID,Name,StudentID,Major,DateTime\n")
        sd_ok = True
        print("SD card ready")
    except Exception as e:
        print("SD card error:", e)


def save_to_sd(uid, name, student_id, major, dt):
    if not sd_ok:
        print("SD not available, skipping save")
        return
    try:
        with open(CSV_PATH, "a") as f:
            f.write("{},{},{},{},{}\n".format(uid, name, student_id, major, dt))
        print("Saved to SD")
    except Exception as e:
        print("SD write error:", e)
def send_to_firestore(uid, name, student_id, major, dt):
    url = ("https://firestore.googleapis.com/v1/projects/{}/databases/(default)"
           "/documents/{}?key={}").format(FIREBASE_PROJECT_ID,
                                          FIRESTORE_COLLECTION,
                                          FIREBASE_API_KEY)
    payload = {
        "fields": {
            "uid":        {"stringValue": uid},
            "name":       {"stringValue": name},
            "student_id": {"stringValue": student_id},
            "major":      {"stringValue": major},
            "datetime":   {"stringValue": dt},
        }
    }
    try:
        res = urequests.post(url,
                             data=ujson.dumps(payload),
                             headers={"Content-Type": "application/json"})
        print("Firestore response:", res.status_code)
        res.close()
    except Exception as e:
        print("Firestore error:", e)


# ---------------- MAIN ----------------
if connect_wifi():
    sync_time()
mount_sd()

print("Scan RFID...")

while True:
    (stat, tag_type) = rdr.request(rdr.REQIDL)

    if stat == rdr.OK:
        (stat, uid) = rdr.anticoll()

        if stat == rdr.OK:
            uid_str = "".join(["{:02X}".format(i) for i in uid])
            print("UID:", uid_str)

            if uid_str in students:
                s = students[uid_str]
                dt = get_datetime()

                print("Valid student:", s["name"], "|", dt)
                beep(0.3)

                save_to_sd(uid_str, s["name"], s["student_id"], s["major"], dt)
                send_to_firestore(uid_str, s["name"], s["student_id"], s["major"], dt)
            else:
                print("Unknown Card")
                beep(3)

            time.sleep(1)
