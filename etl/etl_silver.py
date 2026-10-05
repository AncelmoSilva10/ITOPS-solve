import boto3
import json
from datetime import datetime

s3_client = boto3.client("s3", region_name="us-east-1")

BUCKET_NAME = "bucket-itops-04261081"


# S3

def listar_arquivos():

    resposta = s3_client.list_objects_v2(
        Bucket=BUCKET_NAME,
        Prefix="raw/"
    )

    arqv_antenas = []
    arqv_firewall = []

    for objeto in resposta["Contents"]:

        if objeto["Key"].endswith(".json"):

            if objeto["Key"].endswith("_antena.json"):
                arqv_antenas.append(objeto["Key"])

            elif objeto["Key"].endswith("_firewall.json"):
                arqv_firewall.append(objeto["Key"])

    return arqv_antenas, arqv_firewall


def baixar_arquivos(arquivos):

    files = []

    for arquivo in arquivos:

        files.append(
            s3_client.get_object(
                Bucket=BUCKET_NAME,
                Key=arquivo
            )
        )

    return files


def ler_json(files):

    dados = []

    for arquivo in files:

        file_byte = arquivo["Body"].read()
        file_string = file_byte.decode("UTF-8")
        file_json = json.loads(file_string)

        dados.append(file_json)

    return dados


# Tratamento

def adicionar_chave_minuto(dados):

    for dado in dados:

        data = datetime.strptime(
            dado["timestamp"],
            "%Y-%m-%d %H:%M:%S"
        )

        dado["chave_minuto"] = data.strftime(
            "%Y-%m-%d %H:%M"
        )

    return dados


def agrupar_antenas(dados_antenas):

    antenas_por_minuto = {}

    for antena in dados_antenas:

        minuto = antena["chave_minuto"]

        if minuto not in antenas_por_minuto:

            antenas_por_minuto[minuto] = {
                "bytes_sent_antena": 0,
                "bytes_recv_antena": 0,
                "active_conn_antena": 0,
                "cpu_antena": 0,
                "ram_usage_antena": 0,
                "quantidade_antenas": 0
            }

        antenas_por_minuto[minuto]["bytes_sent_antena"] += antena["bytes_sent"]

        antenas_por_minuto[minuto]["bytes_recv_antena"] += antena["bytes_recv"]

        antenas_por_minuto[minuto]["active_conn_antena"] += antena["active_conn"]

        antenas_por_minuto[minuto]["cpu_antena"] += antena["cpu"]

        antenas_por_minuto[minuto]["ram_usage_antena"] += antena["ram_usage"]

        antenas_por_minuto[minuto]["quantidade_antenas"] += 1

    for minuto, dados in antenas_por_minuto.items():

        quantidade = dados["quantidade_antenas"]

        dados["cpu_antena"] = dados["cpu_antena"] / quantidade

        dados["ram_usage_antena"] = dados["ram_usage_antena"] / quantidade

    return antenas_por_minuto


def criar_lookup_firewall(dados_firewall):

    firewall_por_minuto = {}

    for firewall in dados_firewall:

        firewall_por_minuto[
            firewall["chave_minuto"]
        ] = firewall

    return firewall_por_minuto


def montar_dados_silver(
    antenas_por_minuto,
    firewall_por_minuto
):

    dados_silver = []

    for minuto in sorted(antenas_por_minuto):

        if minuto not in firewall_por_minuto:
            continue

        antenas = antenas_por_minuto[minuto]

        firewall = firewall_por_minuto[minuto]

        linha_silver = {

            "timestamp": minuto,
            "quantidade_antenas": antenas["quantidade_antenas"],
            "bytes_sent_antena": antenas["bytes_sent_antena"],
            "bytes_recv_antena": antenas["bytes_recv_antena"],
            "cpu_antena": antenas["cpu_antena"],
            "ram_usage_antena": antenas["ram_usage_antena"],
            "active_conn_antena": antenas["active_conn_antena"],
            "cpu_firewall": firewall["cpu"],
            "ram_usage_firewall": firewall["ram_usage"],
            "bytes_sent_firewall": firewall["bytes_sent"],
            "bytes_recv_firewall": firewall["bytes_recv"],
            "active_sessions_firewall": firewall["active_sessions"],
            "dropped_packets_firewall": firewall["dropped_packets"],
            "top_blocked_ip_firewall": firewall["top_blocked_ip"]
        }

        dados_silver.append(linha_silver)

    return dados_silver


# Regras de negócio

def adicionar_status(dados_silver):

    for linha in dados_silver:

        if linha["active_conn_antena"] > 40:
            linha["status_conexoes"] = "ALTA_DENSIDADE"
        else:
            linha["status_conexoes"] = "BAIXA_DENSIDADE"

        if linha["cpu_antena"] > 80:
            linha["status_cpu"] = "GARGALO_PROCESSAMENTO"
        else:
            linha["status_cpu"] = "NORMAL"

        if linha["ram_usage_antena"] > 75:
            linha["status_ram"] = "OOM"
        else:
            linha["status_ram"] = "NORMAL"

    return dados_silver


def calcular_throughput(dados_silver):

    for i in range(len(dados_silver)):

        if i == 0:
            dados_silver[i]["throughput_mbps"] = None
            continue

        linha_atual = dados_silver[i]

        linha_anterior = dados_silver[i - 1]

        bytes_diferenca = (
            linha_atual["bytes_sent_antena"]
            - linha_anterior["bytes_sent_antena"]
        )

        throughput_mbps = (
            bytes_diferenca * 8 / 60 / 1000000
        )

        linha_atual["throughput_mbps"] = throughput_mbps

    return dados_silver


def calcular_diferenca_wan(dados_silver):

    for linha in dados_silver:

        linha["diferenca_bytes_wan"] = (
            linha["bytes_sent_firewall"]
            - linha["bytes_sent_antena"]
        )

    return dados_silver


def main():

    arqv_antenas, arqv_firewall = listar_arquivos()

    files_antenas = baixar_arquivos(arqv_antenas)

    files_firewall = baixar_arquivos(arqv_firewall)

    dados_antenas = ler_json(files_antenas)

    dados_firewall = ler_json(files_firewall)

    dados_antenas = adicionar_chave_minuto(dados_antenas)

    dados_firewall = adicionar_chave_minuto(dados_firewall)

    antenas_por_minuto = agrupar_antenas(dados_antenas)

    firewall_por_minuto = criar_lookup_firewall(
        dados_firewall
    )

    dados_silver = montar_dados_silver(
        antenas_por_minuto,
        firewall_por_minuto
    )

    dados_silver = adicionar_status(dados_silver)

    dados_silver = calcular_throughput(dados_silver)

    dados_silver = calcular_diferenca_wan(dados_silver)




main()