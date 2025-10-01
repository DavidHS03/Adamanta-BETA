import os
import cv2
import requests
from pyzbar.pyzbar import decode
from requests.auth import HTTPDigestAuth
from xml.etree import ElementTree as ET
from dotenv import load_dotenv
load_dotenv()


# 🔹 Variables de entorno
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
URL_LOCAL = os.getenv("URL_LOCAL")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

HEADERS = {"Authorization": API_KEY, "Content-Type": "application/json"}


# 🔓 Función para abrir el torniquete vía ISAPI (Hikvision)
def open_turnstile():
    url = f"{URL_LOCAL}/ISAPI/AccessControl/RemoteControl/door/1"

    xml_data = """
    <RemoteControlDoor>
        <cmd>open</cmd>
    </RemoteControlDoor>
    """
    xml_tree = ET.ElementTree(ET.fromstring(xml_data))

    try:
        response = requests.put(
            url,
            auth=HTTPDigestAuth(USERNAME, PASSWORD),
            headers={"Content-Type": "application/xml"},
            data=ET.tostring(xml_tree.getroot(), encoding="utf-8", method="xml"),
            timeout=5,
        )
        if response.status_code == 200:
            print("✅ Torniquete abierto correctamente")
            return True
        else:
            print("⛔ Error al abrir torniquete")
            print("Código:", response.status_code)
            print("Respuesta:", response.text)
            return False
    except Exception as e:
        print("⛔ Error al conectar con el torniquete:", str(e))
        return False


def check_in(unique_code):
    url = f"{BASE_URL}/checkIn?uniqueCode={unique_code}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        return r.json()
    except Exception as e:
        print("⛔ Error en check_in:", str(e))
        return {}


def check_available(unique_code, serial_number="abc123", access_dir=0):
    url = f"{BASE_URL}/checkAvailable"
    payload = {
        "uniqueCode": unique_code,
        "serialNumber": serial_number,
        "accessDir": access_dir,
        "version": 4,
        "mediaType": 0,
    }
    try:
        r = requests.post(url, json=payload, headers=HEADERS, timeout=5)
        data = r.json()

        if data.get("error", {}).get("code") == 0:
            print("✅ Acceso permitido, abriendo puerta...")
            open_turnstile()
        else:
            print("⛔ Acceso denegado:", data.get("error", {}).get("message"))

        return data
    except Exception as e:
        print("⛔ Error en check_available:", str(e))
        return {}


def do_consume(guid):
    url = f"{BASE_URL}/doConsume"
    payload = {"guid": guid}
    try:
        r = requests.post(url, json=payload, headers=HEADERS, timeout=5)
        return r.json()
    except Exception as e:
        print("⛔ Error en do_consume:", str(e))
        return {}


# 🔹 Escanear QR desde cámara
def scan_qr_from_camera():
    cap = cv2.VideoCapture(0)  # 0 = cámara por defecto
    unique_code = None

    print("📷 Escanea el QR con la cámara. Presiona 'q' para salir.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("⛔ No se pudo acceder a la cámara")
            break

        codes = decode(frame)
        for code in codes:
            unique_code = code.data.decode("utf-8")
            print(f"✅ QR detectado: {unique_code}")
            cap.release()
            cv2.destroyAllWindows()
            return unique_code

        cv2.imshow("Escáner QR - Presiona 'q' para salir", frame)

        # salir con tecla "q"
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    return None


# 🔹 Flujo principal
if __name__ == "__main__":
    print("=== Test Turnstile API con QR desde cámara ===")

    unique_code = scan_qr_from_camera()
    if not unique_code:
        exit()

    print("\n1️⃣ Check In:")
    print(check_in(unique_code))

    print("\n2️⃣ Check Available:")
    resp = check_available(unique_code)

    if resp.get("error", {}).get("code") == 0:
        guid = resp["data"].get("guid")
        if guid:
            print("\n3️⃣ Do Consume:")
            print(do_consume(guid))
    else:
        print("\n⛔ Código no válido para acceso")
