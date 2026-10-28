#!/usr/bin/env python3
"""Exercise the real MQTT parser in disposable containers on an internal network.

No host ports are exposed and no existing greenhouse service is restarted.
"""
import json
from pathlib import Path
import subprocess
import tempfile
import time
from uuid import uuid4

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent


def docker(*arguments):
    return subprocess.run(['docker', *arguments], check=True, capture_output=True, text=True)


def main():
    credentials = {**dotenv_values(ROOT / '.env.example'), **dotenv_values(ROOT / '.env')}
    network = 'iot-audit-' + uuid4().hex[:8]
    broker, consumer = network + '-broker', network + '-telegraf'
    process = None
    with tempfile.TemporaryDirectory(prefix='iot-mqtt-check-') as temp:
        directory = Path(temp)
        directory.chmod(0o755)
        (directory / 'broker.conf').write_text(
            'listener 1883\nallow_anonymous false\npassword_file /audit/passwd\n'
            'persistence false\nlog_dest stdout\n')
        config = (ROOT / 'config/telegraf/telegraf.conf').read_text()
        # Retain the exact MQTT input/parser; remove external InfluxDB output.
        (directory / 'telegraf.conf').write_text(
            config[:config.index('[[outputs.influxdb_v2]]')] + config[config.index('[[inputs.mqtt_consumer]]'):])
        try:
            docker('network', 'create', '--internal', network)
            docker('run', '-d', '--name', broker, '--network', network, '--network-alias', 'mosquitto',
                   '-v', str(directory / 'broker.conf') + ':/audit/broker.conf:ro',
                   '-v', str(ROOT / 'config/mosquitto/passwd') + ':/audit/passwd:ro',
                   'eclipse-mosquitto:2.0.18', 'mosquitto', '-c', '/audit/broker.conf')
            process = subprocess.Popen([
                'docker', 'run', '--rm', '--name', consumer, '--network', network,
                '-e', 'MQTT_USERNAME=' + credentials['TELEGRAF_MQTT_USERNAME'],
                '-e', 'MQTT_PASSWORD=' + credentials['TELEGRAF_MQTT_PASSWORD'],
                '-v', str(directory / 'telegraf.conf') + ':/audit/telegraf.conf:ro',
                'telegraf:1.30.0-alpine', 'telegraf', '--test', '--test-wait', '8',
                '--config', '/audit/telegraf.conf'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            time.sleep(2)
            samples = [
                ('ESP32', 'invernadero/telemetria/microclima', {'nodo_id': 'audit', 'temp_aire': 18, 'hum_aire': 75, 'vpd_kpa': 0.5}),
                ('BACKEND', 'invernadero/telemetria/pid', {'nodo_id': 'audit', 'sp_temp': 18, 'sp_hum': 75, 'pv_temp': 17, 'cv_salida': 30}),
                ('BACKEND', 'invernadero/riesgo/indice', {'score_riesgo': 0.8, 'horas_hoja_humeda': 11}),
            ]
            for role, topic, payload in samples:
                docker('exec', broker, 'mosquitto_pub', '-h', '127.0.0.1',
                       '-u', credentials[role + '_MQTT_USERNAME'], '-P', credentials[role + '_MQTT_PASSWORD'],
                       '-t', topic, '-m', json.dumps(payload), '-q', '1')
            stdout, stderr = process.communicate(timeout=20)
            metrics = [line for line in stdout.splitlines() if line.startswith('> ')]
            if (process.returncode or len(metrics) != 3 or
                    not all(line.startswith('> telemetria,') for line in metrics) or
                    'score_riesgo=0.8' not in stdout or 'sp_humedad=75' not in stdout):
                raise RuntimeError('MQTT/Telegraf: validación fallida\n' + stdout + stderr)
            print(stdout, end='')
            print('MQTT autenticado → Telegraf: correcto (3 métricas, red aislada).')
        finally:
            for container in (consumer, broker):
                subprocess.run(['docker', 'rm', '-f', container], capture_output=True)
            if process is not None:
                process.communicate(timeout=10)
            subprocess.run(['docker', 'network', 'rm', network], capture_output=True)


if __name__ == '__main__':
    main()
