import asyncio
from multiprocessing import Queue
from multiprocessing.managers import DictProxy
from typing import Any


class CoreImpl:
    values_shm: DictProxy  # [str, float]  # shared memory
    command_queue: Queue  # command queue

    def __init__(
        self,
        values_shm: DictProxy,  # [str, float],
        command_queue: Queue,
        author: str,
        title: str,
    ) -> None:
        self.values_shm = values_shm
        self.command_queue = command_queue
        self.author = author
        self.title = title

    async def set_motor_angle(self, deg: int) -> None:
        """Servo motorun derecesini ayarlar."""
        self._dispatch_command("Motor açısı", deg)

    async def is_motor_on(self) -> bool:  # Kaldırılacak
        """Motorun açık olup olmadığını döndürür."""
        return False

    async def get_sound_level(self) -> float:  # Kaldırılacak
        """Mikrofonun algıladığı ses seviyesini desibel cinsinden döndürür."""
        return await self._get_input("Ses seviyesi")

    async def get_temperature(self) -> float:
        """Sıcaklık sensörünün aldığı sıcaklık değerini santigrat cinsinden döndürür."""
        return await self._get_input("Sıcaklık")

    async def get_humidity(self) -> float:
        """Nem sensörünün aldığı nem değerini yüzde cinsinden döndürür. (0-100)"""
        return await self._get_input("Nem")

    async def get_ultrasonic_distance(self) -> float:
        """Ultrasonik mesafe sensörü ile ölçülen mesafeyi cm cinsinden döndürür."""
        return await self._get_input("Mesafe")

    async def get_rain(self) -> float:
        """Yağmur sensörünün algıladığı yağmur miktarını yüzde cinsinden döndürür. (0-100)"""
        return await self._get_input("Yağmur")

    async def get_light(self) -> float:
        """LDR sensörünün algıladığı ışık miktarını lümen cinsinden döndürür."""
        return await self._get_input("Işık")

    async def get_gas_amount(self) -> float:
        """Gaz sensörünün algıladığı gaz miktarını ppm cinsinden döndürür."""
        return await self._get_input("Gaz")

    async def get_proximity(self) -> float:
        """Yakın mesafe sensörünün algıladığı mesafeyi cm cinsinden döndürür."""
        return await self._get_input("Yakınlık")

    async def get_air_quality(self) -> float:
        """Hava kalitesi sensörünün algıladığı hava kalitesini AQI cinsinden döndürür."""
        return await self._get_input("Hava Kalitesi")

    async def get_pulse(self) -> float:
        """Nabız sensörünün ölçtüğü nabız değerini BPM cinsinden döndürür."""
        return await self._get_input("Nabız")

    async def get_vibration(self) -> float:
        return await self._get_input("Titreşim")

    async def send_message(self, message: str) -> None:
        """Robot ekranındaki terminale mesaj gönderir.
        Terminaldeki mesajlar, aşağı doğru kayar.
        Eğer yapay zekanızın sonucunu göstermek istiyorsanız bunun yerine `set_state` fonksiyonu kullanabilirsiniz.
        """
        self._dispatch_command("Mesaj", message)

    def sync_send_message(self, message: str) -> None:
        """Internal"""
        self._dispatch_command("Mesaj", message)

    async def set_state(self, state: str) -> None:
        """Yapay zekanızın durumunu günceller.
        Robotun monitöründe herkesin yapay zekasının durumu gösterilir.
        Bu fonksiyonu çağırdığınızda önceki durumunuz silinir ve yeni durumunuz gösterilir.

        Örnek:
        ```python
        forecast = "Güneşli" // Yapay zekanın tahmin etiği hava durumu
        await set_state("Hava durumu: " + forecast)
        ```
        """
        self._dispatch_command("Durum", state)

    async def _get_input(self, label: str) -> Any:
        await asyncio.sleep(0.2)
        value = self.values_shm.get(label, 0)
        return value

    def _dispatch_command(self, verb: str, value: str | int) -> None:
        self.command_queue.put(
            dict(
                author=self.author,
                title=self.title,
                verb=verb,
                value=value,
            )
        )

    async def turn_on_motor(self) -> None:  # Kaldırılacak (1 kişi kullanıyor)
        """Motoru açar. (for compatibility)
        Motoru kapatmak için `turn_off_motor` fonksiyonunu kullanın.
        """
        await self.set_motor_angle(0)
        await asyncio.sleep(0.01)
        await self.set_motor_angle(90)
        await asyncio.sleep(0.01)
        await self.set_motor_angle(180)
        await asyncio.sleep(0.01)
        await self.set_motor_angle(270)
        await asyncio.sleep(0.01)
        await self.set_motor_angle(0)

    async def turn_off_motor(self) -> None:  # Kaldırılacak (1 kişi kullanıyor)
        """Motoru kapatır.
        Motoru açmak için `turn_on_motor` fonksiyonunu kullanın.
        """
        pass
