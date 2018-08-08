# -*- coding: utf-8 -*-

import os
import time

from flask import Flask, jsonify

from . i2c import ComplexSensor, BME280, TSL2561


def gen_app(config_object=None):
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

    sensor = ComplexSensor(
        bme,
        TSL2561(app.config['TSL2561_ADDRESS'])
    )

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
