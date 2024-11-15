import json
from typing import TypedDict


TrasportValues = TypedDict(
    "TrasportValues",
    {
        "Sıcaklık": float,
        "Nem": float,
        "Işık": float,
        "Mesafe": float,
        "Nabız": float,
        "Hava Kalitesi": float,
        "Gaz": float,
        "Titreşim": float,
        # ???
        "Yağmur": float,
        "Yakınlık": float,
    },
)


TransportCommand = TypedDict(
    "TransportCommand",
    {
        "Motor açısı": int,
    },
)


def parse_serial_line(line: str) -> TrasportValues | None:
    try:
        incoming: dict[str, float] = json.loads(line)
        rv = TrasportValues(
            {
                "Sıcaklık": incoming["sicaklik"],
                "Nem": incoming["nem"],
                "Işık": 100 - incoming["isikSeviyesi"],
                "Mesafe": incoming["mesafe"],
                "Nabız": incoming["BPM"],
                "Hava Kalitesi": incoming["havaKalitesi"],
                "Gaz": incoming["gazSeviyesi"],
                "Titreşim": incoming["hareket"],
                # ???
                "Yağmur": incoming["suSeviyesi"],
                "Yakınlık": incoming["mesafe"],
            }
        )
        with open("debug.txt", "w") as f:
            json.dump(rv, f, ensure_ascii=True)
        return rv
    except:
        ...


def stringify_command(command: TransportCommand) -> str | None:
    try:
        motor_angle = command.get("Motor açısı", 0)
        return f"{motor_angle},{motor_angle}"
    except:
        ...
