import boto3
import json
from datetime import datetime
import csv
from io import StringIO

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


def criar_lookup_firewall(dados_firewall):

    firewall_por_minuto = {}

    for firewall in dados_firewall:

        firewall_por_minuto[
            firewall["chave_minuto"]
        ] = firewall

    return firewall_por_minuto


def montar_dados_silver(
    dados_antenas,
    firewall_por_minuto
):

    dados_silver = []

    for antena in dados_antenas:

        minuto = antena["chave_minuto"]

        if minuto not in firewall_por_minuto:
            continue

        firewall = firewall_por_minuto[minuto]

        linha_silver = {

            "timestamp": minuto,

            "id_antena": antena["ID_antena"],

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

    dados_por_minuto = {}

    for linha in dados_silver:

        minuto = linha["timestamp"]

        if minuto not in dados_por_minuto:

            dados_por_minuto[minuto] = {
                "bytes_sent_antena": 0
            }

        dados_por_minuto[minuto]["bytes_sent_antena"] += (
            linha["bytes_sent_antena"]
        )

    minutos = sorted(dados_por_minuto)

    throughput_por_minuto = {}

    for i in range(len(minutos)):

        minuto_atual = minutos[i]

        if i == 0:

            throughput_por_minuto[minuto_atual] = None

            continue

        minuto_anterior = minutos[i - 1]

        bytes_diferenca = (
            dados_por_minuto[minuto_atual]["bytes_sent_antena"]
            - dados_por_minuto[minuto_anterior]["bytes_sent_antena"]
        )

        throughput_mbps = (
            bytes_diferenca * 8 / 60 / 1000000
        )

        throughput_por_minuto[minuto_atual] = throughput_mbps

    for linha in dados_silver:

        linha["throughput_mbps"] = (
            throughput_por_minuto[linha["timestamp"]]
        )

    return dados_silver


def calcular_diferenca_wan(dados_silver):

    dados_por_minuto = {}

    for linha in dados_silver:

        minuto = linha["timestamp"]

        if minuto not in dados_por_minuto:

            dados_por_minuto[minuto] = {
                "bytes_sent_antena": 0,
                "bytes_sent_firewall": linha["bytes_sent_firewall"]
            }

        dados_por_minuto[minuto]["bytes_sent_antena"] += (
            linha["bytes_sent_antena"]
        )

    for linha in dados_silver:

        minuto = linha["timestamp"]

        linha["diferenca_bytes_wan"] = (
            dados_por_minuto[minuto]["bytes_sent_firewall"]
            - dados_por_minuto[minuto]["bytes_sent_antena"]
        )

    return dados_silver


def criar_csv(dados_silver):

    arquivo_csv = StringIO()

    campos = dados_silver[0].keys()

    escritor = csv.DictWriter(
        arquivo_csv,
        fieldnames=campos
    )

    escritor.writeheader()

    escritor.writerows(dados_silver)

    return arquivo_csv.getvalue()


def enviar_silver(dados_silver):

    dados_csv = criar_csv(dados_silver)

    momento_captura = datetime.now()

    nome_arquivo = momento_captura.strftime(
        "%Y-%m-%d_%H-%M"
    )

    nome_arquivo = nome_arquivo + "_silver.csv"

    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key="trusted/" + nome_arquivo,
        Body=dados_csv
    )

    print(
        f"Arquivo enviado para Silver: {nome_arquivo}"
    )


def main():

    arqv_antenas, arqv_firewall = listar_arquivos()

    files_antenas = baixar_arquivos(
        arqv_antenas
    )

    files_firewall = baixar_arquivos(
        arqv_firewall
    )

    dados_antenas = ler_json(
        files_antenas
    )

    dados_firewall = ler_json(
        files_firewall
    )

    dados_antenas = adicionar_chave_minuto(
        dados_antenas
    )

    dados_firewall = adicionar_chave_minuto(
        dados_firewall
    )

    firewall_por_minuto = criar_lookup_firewall(
        dados_firewall
    )

    dados_silver = montar_dados_silver(
        dados_antenas,
        firewall_por_minuto
    )

    dados_silver = adicionar_status(
        dados_silver
    )

    dados_silver = calcular_throughput(
        dados_silver
    )

    dados_silver = calcular_diferenca_wan(
        dados_silver
    )

    enviar_silver(
        dados_silver
    )


main()