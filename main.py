from serial import Serial, serial_for_url
from loader import load


if __name__ == "__main__":
    serial = None # serial_for_url("socket://127.0.0.1:6800")

    def on_any(*args):
        print("==============================")
        print(args)
        # exit()

    load.load(serial=serial, on_message=on_any, on_state_change=on_any, ignore_deaths=True)
