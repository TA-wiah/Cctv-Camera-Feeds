import cv2
import socket
from scapy.all import ARP, Ether, srp
import threading
import queue

# Define standard RTSP ports to check
RTSP_PORTS = [554, 8554]

def scan_network():
    # Scan the local network for devices
    ip_range = "192.168.1.1/24"  # Change this to your network's IP range
    arp = ARP(pdst=ip_range)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether/arp
    result = srp(packet, timeout=2, verbose=False)[0]

    devices = []
    for sent, received in result:
        devices.append(received.psrc)
    
    return devices

def check_rtsp(ip, port, q):
    rtsp_url = f"rtsp://{ip}:{port}/"
    cap = cv2.VideoCapture(rtsp_url)
    if cap.isOpened():
        q.put(rtsp_url)
    cap.release()

def discover_rtsp_streams():
    devices = scan_network()
    q = queue.Queue()
    threads = []

    for ip in devices:
        for port in RTSP_PORTS:
            thread = threading.Thread(target=check_rtsp, args=(ip, port, q))
            threads.append(thread)
            thread.start()

    for thread in threads:
        thread.join()

    streams = []
    while not q.empty():
        streams.append(q.get())
    
    return streams

def main():
    print("Scanning for available RTSP streams...")
    streams = discover_rtsp_streams()

    if not streams:
        print("No RTSP streams found.")
        return

    print("Available RTSP streams:")
    for i, stream in enumerate(streams):
        print(f"{i+1}: {stream}")

    choice = int(input("Enter the number of the stream to view: ")) - 1

    if choice < 0 or choice >= len(streams):
        print("Invalid choice.")
        return

    rtsp_url = streams[choice]
    cap = cv2.VideoCapture(rtsp_url)

    if not cap.isOpened():
        print("Error: Could not open RTSP stream. Please check the URL.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Cannot receive frame (stream end?). Exiting ...")
            break

        cv2.imshow('CCTV Feed', frame)

        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
