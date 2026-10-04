import boto3
import json
from datetime import datetime

s3_client = boto3.client("s3", region_name = "us-east-1")

BUCKET_NAME = "bucket-itops-04261081"

resposta = s3_client.list_objects_v2(
    Bucket = BUCKET_NAME,
    Prefix = "raw/"
)

arqv_antenas = []
arqv_firewall = []

for objeto in resposta["Contents"]:
    
    if objeto["Key"].endswith(".json"):
        if objeto["Key"].endswith("_antena.json"):
            arqv_antenas.append(objeto["Key"])
        elif objeto["Key"].endswith("_firewall.json"):
            arqv_firewall.append(objeto["Key"])


files_antenas = []

for i in arqv_antenas:
    files_antenas.append(s3_client.get_object(
        Bucket = BUCKET_NAME,
        Key = i
        )
    )
    
files_firewall = []

for i in arqv_firewall:
    files_firewall.append(
        s3_client.get_object(
            Bucket=BUCKET_NAME,
            Key=i
        )
    )
 
dados_antenas = [] 
dados_firewall = []

for arquivo in files_antenas:
    file_byte = arquivo["Body"].read()
    file_string = file_byte.decode("UTF-8")        
    file_json = json.loads(file_string)
    dados_antenas.append(file_json)
      
for arquivo in files_firewall:
    file_byte = arquivo["Body"].read()
    file_string = file_byte.decode("UTF-8")        
    file_json = json.loads(file_string)
    dados_firewall.append(file_json)      



linha_silver = {
    "ID_ANTENA":dados_antenas[0]["ID_ANTENA"],
    "timestamp":dados_antenas[0]["timestamp"],
    "bytes_sent_antena":dados_antenas[0]["bytes_sent"],
    "bytes_recv_antena":dados_antenas[0]["bytes_recv"],
    "cpu_antena":dados_antenas[0]["cpu"],
    "ram_usage_antena":dados_antenas[0]["ram_usage"],
    "active_conn_antena":dados_antenas[0]["active_conn"],
    "timestamp_firewall":dados_firewall[0]["timestamp"],
    "cpu_firewall":dados_firewall[0]["cpu"],
    "ram_usage_firewall":dados_firewall[0]["ram_usage"],
    "bytes_sent_firewall":dados_firewall[0]["bytes_sent"],
    "bytes_recv_firewall":dados_firewall[0]["bytes_recv"],
    "active_sessions_firewall":dados_firewall[0]["active_sessions"],
    "dropped_packets_firewall":dados_firewall[0]["dropped_packets"],
    "top_blocked_ip_firewall":dados_firewall[0]["top_blocked_ip"]
}

for antena in dados_antenas:
    data = datetime.strptime(antena["timestamp"],"%Y-%m-%d %H:%M:%S")
    chave_minuto = data.strftime("%Y-%m-%d %H:%M")
    antena["chave_minuto"] = chave_minuto

for firewall in dados_firewall:
    data = datetime.strptime(firewall["timestamp"],"%Y-%m-%d %H:%M:%S")
    chave_minuto = data.strftime("%Y-%m-%d %H:%M")
    firewall["chave_minuto"] = chave_minuto


firewall_por_minuto = {}
for firewall in dados_firewall:
    firewall_por_minuto[firewall["chave_minuto"]] = firewall
    
dados_silver = []

for antena in dados_antenas:

    firewall = firewall_por_minuto[antena["chave_minuto"]]

    linha_silver = {
        "ID_ANTENA": antena["ID_ANTENA"],
        "timestamp": antena["timestamp"],

        "bytes_sent_antena": antena["bytes_sent"],
        "bytes_recv_antena": antena["bytes_recv"],
        "cpu_antena": antena["cpu"],
        "ram_usage_antena": antena["ram_usage"],
        "active_conn_antena": antena["active_conn"],

        "cpu_firewall": firewall["cpu"],
        "ram_usage_firewall": firewall["ram_usage"],
        "bytes_sent_firewall": firewall["bytes_sent"],
        "bytes_recv_firewall": firewall["bytes_recv"],
        "active_sessions_firewall": firewall["active_sessions"],
        "dropped_packets_firewall": firewall["dropped_packets"],
        "top_blocked_ip_firewall": firewall["top_blocked_ip"]
    }

    dados_silver.append(linha_silver)
    
for linha in dados_silver:
    if linha["active_conn_antena"] > 40:
        linha["status_carga"] = "ALTA_DENSIDADE"
    else:
        linha ["status_carga"] = "BAIXA_DENSIDADE"

