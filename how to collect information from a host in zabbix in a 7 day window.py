import json
import datetime
from pyzabbix import ZabbixAPI
import logging


ZABBIX_SERVER = '####URL####'
ZABBIX_API_TOKEN = '###################'  # Reemplaza con tu token de API

# logging para ver como va 
logging.basicConfig(filename='zabbix_script.log', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

zapi = ZabbixAPI(ZABBIX_SERVER)
zapi.login(api_token=ZABBIX_API_TOKEN)

# Lee los hosts desde un archivo txt
with open('hosts.txt', 'r') as file:
    hosts = file.read().splitlines()

# obtener el tiempo de 7 dias , nose usar otra forma xd
time_till = int(datetime.datetime.now().timestamp())
time_from = time_till - 7 * 24 * 60 * 60

# funcionn para obtener los datos del host
def get_host_data(host):
    result = {}
    try:
        # Obtener el host ID
        host_info = zapi.host.get(filter={"host": host})
        if not host_info:
            logging.warning(f"Host no encontrado: {host}")
            return {host: "Host no encontrado"}

        host_id = host_info[0]['hostid']

        #  obtengo la perdida y latencia en crudo
        items = zapi.item.get(hostids=host_id, filter={"key_": ["icmppingloss", "icmppingsec"]})
        item_ids = {item['key_']: item['itemid'] for item in items}

        # me aseguro de que se encontraron las cosas q necesitoo
        if "icmppingloss" not in item_ids or "icmppingsec" not in item_ids:
            logging.warning(f"Items de latencia o pérdida de paquetes no encontrados para el host: {host}")
            return {host: "Items de latencia o pérdida de paquetes no encontrados"}

        # obtengo los datos q quiero, en este caso 7 diasss
        packet_loss_data = zapi.history.get(itemids=item_ids["icmppingloss"], time_from=time_from, time_till=time_till, history=0)
        latency_data = zapi.history.get(itemids=item_ids["icmppingsec"], time_from=time_from, time_till=time_till, history=0)

        # Calcular promedios
        packet_loss_avg = sum(float(record['value']) for record in packet_loss_data) / len(packet_loss_data) if packet_loss_data else 0
        latency_avg = sum(float(record['value']) for record in latency_data) / len(latency_data) if latency_data else 0

        result = {
            "host": host,
            "packet_loss_avg": packet_loss_avg,
            "latency_avg": latency_avg
        }
        logging.info(f"Datos obtenidos para el host: {host}")
    except Exception as e:
        logging.error(f"Error al obtener datos para el host {host}: {e}")
        result = {host: f"Error al obtener datos: {str(e)}"}

    return result

# junto los datos para todos los hosts
results = []
for host in hosts:
    host_data = get_host_data(host)
    results.append(host_data)

# escribo los resultados en un archivo de salida
with open('resultados.txt', 'w') as output_file:
    for result in results:
        output_file.write(json.dumps(result) + '\n')

print("Proceso completado. Resultados guardados en 'resultados.txt'.")
