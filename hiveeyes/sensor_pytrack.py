# -*- coding: utf-8 -*-
# (c) 2019 Jan Hoffmann <jan.hoffmann@bergamsee.de>
# (c) 2019 Andreas Motl <andreas@hiveeyes.org>
# License: GNU General Public License, Version 3
from terkin import logging
from terkin.sensor import AbstractSensor


log = logging.getLogger(__name__)


class PytrackSensor(AbstractSensor):
    """
    A Pytrack sensor component.
    """

    def __init__(self):
        super().__init__()

        # The driver instance.
        self.readings = None
        self.bus = None

        self.sensor = None
        self.l76 = None

    def start(self):
        """
        Getting the bus
        """
        if self.bus is None:
            raise KeyError("I2C bus missing")

        # Initialize the hardware driver.
        try:
            from pytrack import Pytrack
            self.sensor = Pytrack(i2c=self.bus.adapter)
        except:
            log.exception('Pytrack hardware driver failed')
            raise

        # Initialize the L76GNS sensor driver.
        try:
            from L76GNSV4 import L76GNSS
            self.l76 = L76GNSS(pytrack=self.sensor, timeout=5)
        except:
            log.exception('Pytrack hardware driver failed')
            raise

    def read(self):
        data = {}
        log.info('Acquire reading from Pytrack')
        data['battery_voltage'] = float(self.sensor.read_battery_voltage())

        # TODO: Add more data here.
        l76_data = self.read_l76gns()
        data.update(l76_data)

        log.info("Pytrack data: {}".format(data))
        return data

    def read_l76gns(self):

        data = {}

        # Call this to start the machinery and actually get a fix.
        try:
            self.l76.coordinates()
        except Exception as e:
            log.exception("Could not read coordinates")
            raise

        # Only read values when having a fix.
        if not self.l76.fixed():
            return data

        # Read speed and orientation.
        try:
            speed = self.l76.get_speed()
            data['speed'] = float(speed.get('speed'))
            data['cog'] = float(speed.get('COG'))
        except Exception as e:
            log.warning("Could not read Speed. Error:", e)

        # Read position.
        try:
            location = self.l76.get_location(MSL=True)
        except Exception as e:
            log.exception("Could not read location from L76 GNSS")

        try:
            data['longitude'] = float(location.get('longitude'))
            data['latitude'] = float(location.get('latitude'))
            data['altitude'] = float(location.get('altitude'))
        except Exception as e:
            log.warning('No GPS Data')

        return data
