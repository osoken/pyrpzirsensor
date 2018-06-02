# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from collections import Iterable

from smbus import SMBus

from . import util


class I2CSensorBase(metaclass=ABCMeta):
    def __init__(self, i2c_addr_):
        super(I2CSensorBase, self).__init__()
        self.__i2c_addr = i2c_addr_
        self.__i2c = SMBus(1)

    def read_address(self, addr_, length_):
        return self.__i2c.read_i2c_block_data(
            self.__i2c_addr, addr_, length_
        )

    def read_address_single(self, addr_):
        return self.read_address(addr_, 1)[0]

    def read_address_twobyte(self, addr_):
        tmp = self.read_address(addr_, 2)
        return tmp[0] + (tmp[1] << 8)

    def read_address_signed16(self, addr_):
        return util.uint16_to_signed16(
            self.read_address_twobyte(addr_)
        )

    def read_address_signed8(self, addr_):
        return util.uint8_to_signed8(
            self.read_address_single(addr_)
        )

    def write_address(self, addr_, data_):
        self.__i2c.write_i2c_block_data(
            self.__i2c_addr, addr_, data_
        )

    def write_address_single(self, addr_, datum_):
        self.write_address(addr_, [datum_])

    def read_bits(self, addr_, offset_, length_):
        """Read bits

        :param addr_: address to read
        :param offset_: 0-7
        :param length_: length to read
        """
        return (self.read_address_single(addr_) >> offset_) &\
            ((1 << length_) - 1)

    def write_bits(self, addr_, datum_, offset_, length_):
        """Write bits

        :param addr_: address to read
        :param datum_: data to write
        :param offset_: 0-7
        :param length_: length to read
        """
        self.write_address_single(
            addr_,
            ((datum_ & ((1 << length_) - 1)) << offset_) |
            (
                self.read_address_single(addr_) &
                (0xFF ^ (((1 << length_) - 1) << offset_))
            )
        )

    @abstractmethod
    def attributes(self):
        pass

    @abstractmethod
    def values(self):
        pass

    def __getitem__(self, attr):
        if attr in self.attributes():
            return getattr(self, attr)
        raise KeyError(attr)


class BME280(I2CSensorBase):
    """Python driver for BME280.
    https://ae-bst.resource.bosch.com/media/_tech/media/datasheets/BST-BME280_DS001-11.pdf

    :param i2c_addr_: I2C address
    """

    oversampling_bits_map = util.BidirectionalMultiDict((
        (0, 0), (1, 1), (2, 2), (4, 3), (8, 4), (16, 5), (16, 6), (16, 7)
    ))
    mode_bits_map = util.BidirectionalMultiDict((
        ('sleep', 0), ('forced', 1), ('forced', 2), ('normal', 3)
    ))
    inactivedurationms_bits_map = util.BidirectionalMultiDict((
        (0.5, 0), (62.5, 1), (125, 2), (250, 3), (500, 4), (1000, 5),
        (10, 6), (20, 7)
    ))
    filter_bits_map = util.BidirectionalMultiDict((
        (0, 0), (2, 1), (4, 2), (8, 3), (16, 4), (16, 5), (16, 6), (16, 7)
    ))

    def __init__(self, i2c_addr_):
        super(BME280, self).__init__(i2c_addr_)
        self.__init_cal()

    def __init_cal(self):
        self.__cal = {}
        self.__cal['dig_T1'] = self.read_address_twobyte(0x88)
        self.__cal['dig_T2'] = self.read_address_signed16(0x8A)
        self.__cal['dig_T3'] = self.read_address_signed16(0x8C)
        self.__cal['dig_P1'] = self.read_address_twobyte(0x8E)
        self.__cal['dig_P2'] = self.read_address_signed16(0x90)
        self.__cal['dig_P3'] = self.read_address_signed16(0x92)
        self.__cal['dig_P4'] = self.read_address_signed16(0x94)
        self.__cal['dig_P5'] = self.read_address_signed16(0x96)
        self.__cal['dig_P6'] = self.read_address_signed16(0x98)
        self.__cal['dig_P7'] = self.read_address_signed16(0x9A)
        self.__cal['dig_P8'] = self.read_address_signed16(0x9C)
        self.__cal['dig_P9'] = self.read_address_signed16(0x9E)
        self.__cal['dig_H1'] = self.read_address_single(0xA1)
        self.__cal['dig_H2'] = self.read_address_signed16(0xE1)
        self.__cal['dig_H3'] = self.read_address_single(0xE3)
        self.__cal['dig_H4'] = util.uint16_to_signed16(
            (self.read_address_single(0xE4) << 4) +
            (self.read_address_single(0xE5) & 0x0F)
        )
        self.__cal['dig_H5'] = util.uint16_to_signed16(
            self.read_address_twobyte(0xE5) >> 4
        )
        self.__cal['dig_H6'] = self.read_address_signed8(0xE7)

    def __get_oversampling(self, addr_, offset_):
        d = self.read_bits(addr_, offset_, 3)
        return self.oversampling_bits_map.inverse[d]

    def get_humidity_oversampling(self):
        return self.__get_oversampling(0xF2, 0)

    def get_temperature_oversampling(self):
        return self.__get_oversampling(0xF4, 5)

    def get_pressure_oversampling(self):
        return self.__get_oversampling(0xF4, 2)

    def __set_oversampling(self, addr_, offset_, value_):
        if value_ not in self.oversampling_bits_map:
            raise ValueError(value_)
        self.write_bits(addr_, self.oversampling_bits_map[value_], offset_, 3)

    def set_humidity_oversampling(self, value_):
        """set oversampling of humidity data

        :param value_: one of ``0`` (means skipped), ``1``, ``2``, ``4``,\
        ``8``, ``16``
        """
        self.__set_oversampling(0xF2, 0, value_)

    def set_temperature_oversampling(self, value_):
        """set oversampling of temperature data

        :param value_: one of ``0`` (means skipped), ``1``, ``2``, ``4``,\
        ``8``, ``16``
        """
        self.__set_oversampling(0xF4, 5, value_)

    def set_pressure_oversampling(self, value_):
        """set oversampling of pressure data

        :param value_: one of ``0`` (means skipped), ``1``, ``2``, ``4``,\
        ``8``, ``16``
        """
        self.__set_oversampling(0xF4, 2, value_)

    def get_mode(self):
        d = self.read_bits(0xF4, 0, 2)
        return self.mode_bits_map.inverse[d]

    def set_mode(self, mode_):
        """set sensor mode

        :param mode_: one of ``'sleep'``, ``'forced'``, ``'normal'``
        """
        if mode_ not in self.mode_bits_map:
            raise ValueError(mode_)
        self.write_bits(0xF4, self.mode_bits_map[mode_], 0, 2)

    def get_inactive_duration(self):
        d = self.read_bits(0xF5, 5, 3)
        return self.inactivedurationms_bits_map.inverse[d]

    def set_inactive_duration(self, duration_ms_):
        """set inactive duration in normal mode

        :param duration_ms_: one of ``0.5``, ``62.5``, ``125``, ``250``,\
        ``500``, ``1000``, ``10``, ``20``
        """
        if duration_ms_ not in self.inactivedurationms_bits_map:
            raise ValueError(duration_ms_)
        self.write_bits(
            0xF5, self.inactivedurationms_bits_map[duration_ms_], 5, 3
        )

    def get_filter(self):
        d = self.read_bits(0xF5, 2, 3)
        return self.filter_bits_map.inverse[d]

    def set_filter(self, value_):
        """set filter value

        :param value_: one of ``0`` (means filter off), ``2``, ``4``,\
        ``8``, ``16``
        """
        if value_ not in self.filter_bits_map:
            raise ValueError(value_)
        self.write_bits(0xF5, self.filter_bits_map[value_], 2, 3)

    def print_cal(self):
        for k, v in sorted(self.__cal.items(), key=lambda x: x[0]):
            print(' {} : {}'.format(k, v))

    def get_t_fine(self, adc_t=None):
        if adc_t is None:
            return self.get_t_fine(self.get_adc_t())
        return ((
            (((adc_t >> 3) - (self.__cal['dig_T1'] << 1))) *
            (self.__cal['dig_T2'])
        ) >> 11) + ((((
            ((adc_t >> 4) - (self.__cal['dig_T1'])) *
            ((adc_t >> 4) - (self.__cal['dig_T1']))
        ) >> 12) * (self.__cal['dig_T3'])) >> 14)

    def get_adc_t(self):
        data = self.read_address(0xFA, 3)
        return (data[0] << 12) + (data[1] << 4) + (data[2] >> 4)

    def get_adc_p(self):
        data = self.read_address(0xF7, 3)
        return (data[0] << 12) + (data[1] << 4) + (data[2] >> 4)

    def get_adc_h(self):
        data = self.read_address(0xFD, 2)
        return (data[0] << 8) + data[1]

    def get_temperature(self, t_fine=None, adc_t=None):
        if t_fine is None:
            return self.get_temperature(self.get_t_fine(adc_t), adc_t)
        return ((t_fine * 5 + 128) >> 8) * 0.01

    def get_pressure(self, t_fine=None, adc_p=None, adc_t=None):
        if t_fine is None:
            return self.get_pressure(self.get_t_fine(adc_t), adc_p, adc_t)
        if adc_p is None:
            return self.get_pressure(t_fine, self.get_adc_p(), adc_t)
        var1 = t_fine - 128000
        var2 = var1 * var1 * self.__cal['dig_P6']
        var2 = var2 + ((var1 * self.__cal['dig_P5']) << 17)
        var2 = var2 + (self.__cal['dig_P4'] << 35)
        var1 = ((var1 * var1 * self.__cal['dig_P3']) >> 8) + \
            ((var1 * self.__cal['dig_P2']) << 12)
        var1 = (((1 << 47) + var1)) * (self.__cal['dig_P1']) >> 33
        if var1 == 0:
            return 0
        p = 1048576 - adc_p
        p = (((p << 31) - var2) * 3125) // var1
        var1 = (self.__cal['dig_P9'] * (p >> 13) * (p >> 13)) >> 25
        var2 = (self.__cal['dig_P8'] * p) >> 19
        p = ((p + var1 + var2) >> 8) + ((self.__cal['dig_P7']) << 4)
        return p / 25600

    def get_humidity(self, t_fine=None, adc_h=None, adc_t=None):
        if t_fine is None:
            return self.get_humidity(self.get_t_fine(adc_t), adc_h, adc_t)
        if adc_h is None:
            return self.get_humidity(t_fine, self.get_adc_h(), adc_t)
        v_x1_u32r = (t_fine - 76800)
        v_x1_u32r = ((((
            (adc_h << 14) - ((self.__cal['dig_H4']) << 20) -
            ((self.__cal['dig_H5']) * v_x1_u32r)
        ) + 16384) >> 15) * (((((
            ((v_x1_u32r * self.__cal['dig_H6']) >> 10) *
            (((v_x1_u32r * self.__cal['dig_H3']) >> 11) + 32768)
        ) >> 10) + 2097152) * self.__cal['dig_H2'] + 8192) >> 14))
        v_x1_u32r = (v_x1_u32r - (((
            ((v_x1_u32r >> 15) * (v_x1_u32r >> 15)) >> 7
        ) * self.__cal['dig_H1']) >> 4))
        if v_x1_u32r < 0:
            v_x1_u32r = 0
        if v_x1_u32r > 419430400:
            v_x1_u32r = 419430400
        return (v_x1_u32r >> 12) / 1024

    @property
    def temperature(self):
        return self.get_temperature()

    @property
    def humidity(self):
        return self.get_humidity()

    @property
    def pressure(self):
        return self.get_pressure()

    def get_adc(self):
        data = self.read_address(0xF7, 8)
        return (
            (data[0] << 12) + (data[1] << 4) + (data[2] >> 4),
            (data[3] << 12) + (data[4] << 4) + (data[5] >> 4),
            (data[6] << 8) + data[7]
        )

    def attributes(self):
        return ('pressure', 'temperature', 'humidity')

    def values(self):
        (adc_p, adc_t, adc_h) = self.get_adc()
        t_fine = self.get_t_fine(adc_t)
        return (
            self.get_pressure(t_fine, adc_p, adc_t),
            self.get_temperature(t_fine, adc_t),
            self.get_humidity(t_fine, adc_h, adc_t)
        )


class TSL2561(I2CSensorBase):
    """Python driver for TSL2561.
    https://cdn-shop.adafruit.com/datasheets/TSL2561.pdf

    :param i2c_addr_: I2C address
    """
    def __init__(self, i2c_addr_):
        super(TSL2561, self).__init__(i2c_addr_)

    def read_address(self, addr_, length_, default_=0):
        return super(TSL2561, self).read_address(
            addr_ | 0x80, length_, default_
        )

    def write_address(self, addr_, data_):
        super(TSL2561, self).write_address(addr_ | 0x80, data_)

    def attributes(self):
        return ('illuminance', )

    def values(self):
        return (0.0, )

    def get_illuminance(self):
        return 0.0

    @property
    def illuminance(self):
        return self.get_illuminance()


class ComplexSensor(object):
    def __init__(self, *sensors):
        super(ComplexSensor, self).__init__()
        self.__sensors = []
        self.__register_sensors(sensors)

    def __register_sensors(self, s):
        if isinstance(s, I2CSensorBase):
            self.__sensors.append(s)
        else:
            if isinstance(s, Iterable):
                for d in s:
                    self.__register_sensors(d)
            else:
                raise TypeError(s)

    def attributes(self):
        return sum(map(lambda x: x.attributes(), self.__sensors), tuple())

    def values(self):
        return sum(map(lambda x: x.values(), self.__sensors), tuple())

    def __getitem__(self, attr):
        for s in self.__sensors:
            if attr in s.attributes():
                return s[attr]
        raise KeyError(attr)
