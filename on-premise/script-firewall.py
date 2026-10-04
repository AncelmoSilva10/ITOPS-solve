import psutil
import random
from datetime import datetime
import json
import boto3
import time

s3_client = boto3.client("s3", region_name = "us-east-1")

BUCKET_NAME = "bucket-itops-04261081"


def capturar_dados():
    momento_captura = datetime.now()
    timestamp = momento_captura.strftime("%Y-%m-%d %H:%M:%S")
    cpu = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent
    dados_rede = psutil.net_io_counters()
    bytes_sent = dados_rede.bytes_sent
    bytes_recv = dados_rede.bytes_recv
    active_sessions = random.randint(1, 500)
    dropped_packets = random.randint(100, 600)
    if dropped_packets <= 300:
        top_blocked_ip = None
    else:
        top_blocked_ip = "192.168.1.50"
    
    firewall = {
        "timestamp":timestamp,
        "cpu":cpu,
        "ram_usage":ram_usage,
        "bytes_sent":bytes_sent,
        "bytes_recv":bytes_recv,
        "active_sessions":active_sessions,
        "dropped_packets":dropped_packets,
        "top_blocked_ip":top_blocked_ip
    }
    return firewall, momento_captura


def enviar_arquivos():
    dados, momento_captura = capturar_dados()
    nome_arquivo = momento_captura.strftime("%Y-%m-%d_%H-%M")
    nome_arquivo = nome_arquivo+"_firewall.json"
    
    dados_json = json.dumps(dados)
    

    s3_client.put_object(
        Bucket = BUCKET_NAME,
        Key = "raw/"+nome_arquivo,
        Body = dados_json
    )

    print(f"Arquivo enviado do firewall: {nome_arquivo}")

while True:
    enviar_arquivos()
    time.sleep(60)
