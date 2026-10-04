import psutil
import getmac
import random
import json
import boto3
from datetime import datetime


s3_client = boto3.client("s3", region_name = "us-east-1")


BUCKET_NAME = "bucket-itops-04261081"


def capturar_dados():
    ID_ANTENA = getmac.get_mac_address()
    dados_rede = psutil.net_io_counters()
    bytes_sent = dados_rede.bytes_sent
    bytes_recv = dados_rede.bytes_recv
    cpu = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent
    active_conn = random.randint(1, 500)
    
    antena = {
    "ID_ANTENA":ID_ANTENA,
    "bytes_sent":bytes_sent,
    "bytes_recv":bytes_recv,
    "cpu":cpu,
    "ram_usage":ram_usage,
    "active_conn":active_conn    
    }
    
    return antena
    
dados_json = json.dumps(capturar_dados())
momento_captura = datetime.now()
nome_arquivo = momento_captura.strftime("%Y-%m-%d_%H-%m")
nome_arquivo = nome_arquivo+"_ap01.json"


s3_client.put_object(
    Bucket = BUCKET_NAME,
    key = "raw/"+nome_arquivo,
    body = dados_json
)
