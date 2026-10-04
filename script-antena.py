import psutil
import getmac
import random
import json
import boto3
from datetime import datetime
import time


s3_client = boto3.client("s3", region_name = "us-east-1")


BUCKET_NAME = "bucket-itops-04261081"


def capturar_dados():
    ID_ANTENA = getmac.get_mac_address()
    momento_captura = datetime.now()
    timestamp = momento_captura.strftime("%Y-%m-%d %H:%M:%S")
    dados_rede = psutil.net_io_counters()
    bytes_sent = dados_rede.bytes_sent
    bytes_recv = dados_rede.bytes_recv
    cpu = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent
    active_conn = random.randint(1, 500)
    
    antena = {
    "ID_ANTENA":ID_ANTENA,
    "timestamp":timestamp,
    "bytes_sent":bytes_sent,
    "bytes_recv":bytes_recv,
    "cpu":cpu,
    "ram_usage":ram_usage,
    "active_conn":active_conn    
    }
    
    return antena, momento_captura
    
def enviar_arquivo():
    dados, momento_captura = capturar_dados()
    nome_arquivo = momento_captura.strftime("%Y-%m-%d_%H-%m")
    nome_arquivo = nome_arquivo+"_antena.json"
    
    dados_json = json.dumps(dados)


    s3_client.put_object(
        Bucket = BUCKET_NAME,
        Key = "raw/"+nome_arquivo,
        Body = dados_json
    )
    
    print(f"Arquivo enviado da Antena: {nome_arquivo}")
    
while True:
    enviar_arquivo()
    time.sleep(60)
