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


def parse_serial_line(line: str) -> TrasportValues:
    incoming: dict[str, float] = json.loads(line)
    return TrasportValues(
        {
            "Sıcaklık": incoming["sicaklik"],
            "Nem": incoming["nem"],
            "Işık": incoming["isikSeviyesi"],
            "Mesafe": incoming["mesafe"],
            "Nabız": incoming["BPM"],
            "Hava Kalitesi": incoming["havaKalitesi"],
            "Gaz": incoming["gazSeviyesi"],
            "Titreşim": incoming["hareket"],
            # ???
            "Yağmur": 0.0,
            "Yakınlık": 0.0,
        }
    )


def stringify_command(command: TransportCommand) -> str:
    motor_angle = command.get("Motor açısı", 0)
    return f"{motor_angle},{motor_angle}"
