from serial import Serial, serial_for_url
from loader.impl import load


if __name__ == "__main__":
    # serial = Serial("COM3", baudrate=115200)
    # print(serial.read_until().decode("utf-8"))

    def on_any(*args):
        return
        print("==============================")
        print("==============================")
        print(args)
        print("==============================")
        print("==============================")
        exit()

    load.load(
        serial=None, on_message=on_any, on_state_change=on_any, ignore_deaths=True
    )
