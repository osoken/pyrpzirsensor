# -*- coding: utf-8 -*-

import os
import time
import json
from logging.config import dictConfig


from flask import Flask, jsonify

from . i2c import ThreadedCompositeSensor, BME280, TSL2561, TSL2572


def gen_app(config_object=None, logsetting_file=None):
    if logsetting_file is not None:
        with open(logsetting_file, 'r') as fin:
            dictConfig(json.load(fin))
    elif os.getenv('PYRPZIRSENSOR_LOGGER') is not None:
        with open(os.getenv('PYRPZIRSENSOR_LOGGER'), 'r') as fin:
            dictConfig(json.load(fin))
    app = Flask(__name__)
    app.config.from_object('pyrpzirsensor.config')
    if os.getenv('PYRPZIRSENSOR') is not None:
        app.config.from_envvar('PYRPZIRSENSOR')
    if config_object is not None:
        app.config.update(**config_object)

    bme = BME280(app.config['BME280_ADDRESS'])
    bme.set_mode(app.config['BME280_MODE'])
    bme.set_filter(app.config['BME280_FILTER'])
    bme.set_humidity_oversampling(app.config['BME280_HUMIDITY_OVERSAMPLING'])
    bme.set_pressure_oversampling(app.config['BME280_PRESSURE_OVERSAMPLING'])
    bme.set_temperature_oversampling(
        app.config['BME280_TEMPERATURE_OVERSAMPLING']
    )
    bme.set_inactive_duration(app.config['BME280_INACTIVE_DURATION'])

    if app.config['ILLUMINANCE_SENSOR'] == 'TSL2572':
        illuminance_sensor_class = TSL2572
    elif app.config['ILLUMINANCE_SENSOR'] == 'TSL2561':
        illuminance_sensor_class = TSL2561
    else:
        raise Exception(
            'Unknown illuminance sensor: ', app.config['ILLUMINANCE_SENSOR']
        )

    sensor = ThreadedCompositeSensor((
        bme,
        illuminance_sensor_class(app.config['ILLUMINANCE_SENSOR_ADDRESS'])
    ), lambda v: app.logger.info('sensor value.', extra=v))

    @app.route('/api/temperature')
    def api_temperature():
        return jsonify({
            'temperature': sensor['temperature'],
            'timestamp': time.time()
        })

    @app.route('/api/pressure')
    def api_pressure():
        return jsonify({
            'pressure': sensor['pressure'],
            'timestamp': time.time()
        })

    @app.route('/api/humidity')
    def api_humidity():
        return jsonify({
            'humidiry': sensor['humidity'],
            'timestamp': time.time()
        })

    @app.route('/api/illuminance')
    def api_illuminance():
        return jsonify({
            'illuminance': sensor['illuminance'],
            'timestamp': time.time()
        })

    @app.route('/api/sensor')
    def api_sensor():
        return jsonify(dict(
            zip(sensor.attributes(), sensor.values()),
            timestamp=time.time()
        ))

    return app
