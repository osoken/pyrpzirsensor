# pyrpzirsensor

Python [RPZ-IR-Sensor](http://indoor.lolipop.jp/IndoorCorgiElec/RPZ-IR-Sensor.php) Utility.

## Setup

### Raspberry-Pi Basic settings

Enable I2C.

```
$ sudo raspi-config
```

- [Interfacing Options] - [I2C] - [Yes]

Install required packages.

```shell
$ sudo apt update
$ sudo apt -y dist-upgrade
$ sudo apt -y upgrade
$ sudo apt install -y git python3-pip python3-smbus python3-flask i2c-tools
```

### Clone and install this package

```shell
$ cd
$ mkdir app
$ cd app
$ git clone https://github.com/osoken/pyrpzirsensor.git
$ cd pyrpzirsensor
$ pip3 install -e .
```

## Run the application

```shell
$ python3 -m pyrpzirsensor
```

Then, you can access `http://<your raspi's address>:5000/api/sensor`.
You'll get the JSON response as follows:

```
{
  "humidity": 52.27734375,
  "illuminance": 0,
  "pressure": 1020.976484375,
  "temperature": 25.2,
  "timestamp": 1538734026.4533937
}
```

### Configuration

| attribute name | description  | default value |
| :-- | :-- | :-- |
| `DEBUG` | Flask runs in debug mode or not | `False` |
| `HOST` | Binding for Flask app | `'0.0.0.0'` |
| `BME280_ADDRESS` | BME280 I2C address |  `0x77` |
| `TSL2561_ADDRESS` | TSL2561 I2C address | `0x29` |
| `BME280_MODE` | BME280 running mode | `'normal'` |
| `BME280_FILTER` | BME280 filter size | `16` |
| `BME280_HUMIDITY_OVERSAMPLING` | BME280 oversampling for humidity | `1` |
| `BME280_PRESSURE_OVERSAMPLING` | BME280 oversampling for pressure | `16` |
| `BME280_TEMPERATURE_OVERSAMPLING` | BME280 oversampling for temperature | `2` |
| `BME280_INACTIVE_DURATION` | BME280 inactive duration in ms | `1000` |


These values can be set via a configuration file.
For example, if your BME280 uses `0x76`, you should put a configuraton file,
say `/home/pi/app/app.conf` and write the following:

```
BME280_ADDRESS = 0x76
```

Then, specify that via `PYRPZIRSENSOR` enviromnent variable.

```shell
$ PYRPZIRSENSOR="/home/pi/app/app.conf" python3 -m pyrpzirsensor
```

## Supervisor integration

Install `supervisorctl` command.

```shell
$ sudo apt install supervisor
```

Write the following settings in `/etc/supervisor/conf.d/rpzirsensor.conf`.

```/etc/supervisor/conf.d/rpzirsensor.conf
[program:pyrpzirsensor]
command=python3 -m pyrpzirsensor
numprocs=1
redirect_stderr=true
stdout_logfile=/home/pi/app/pyrpzirsensor.log
user=pi
environment = PYRPZIRSENSOR="/home/pi/app/app.conf"
```

Register `pyrpzirsensor` as a service.

```shell
$ sudo supervisorctl reread
$ sudo supervisorctl add pyrpzirsensor
```

## Logstash integration

Install `python-logstash`.

```
$ pip3 install python-logstash
```

Place JSON config file for logger. Make sure you set the correct value for `handlers.logstash.host`.

```
{
  "version": 1,
  "handlers": {
    "logstash": {
      "level": "INFO",
      "class": "logstash.TCPLogstashHandler",
      "host": <Edit here to point your logstash server>,
      "port": 5000,
      "version": 1,
      "message_type": "logstash",
      "tags": [
        "rpzirsensor"
      ]
    }
  },
  "root": {
    "level": "INFO",
    "handlers": [
      "logstash"
    ]
  }
}
```

Then, specify the log file via `PYRPZIRSENSOR_LOGGER` environment variable.

```/etc/supervisor/conf.d/rpzirsensor.conf
[program:pyrpzirsensor]
command=python3 -m pyrpzirsensor
numprocs=1
redirect_stderr=true
stdout_logfile=/home/pi/app/pyrpzirsensor.log
user=pi
environment = PYRPZIRSENSOR="/home/pi/app/app.conf",PYRPZIRSENSOR_LOGGER="/home/pi/app/logstash.conf.json"
```
