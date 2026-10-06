import boto3
import csv
from io import StringIO
from datetime import datetime

s3_client = boto3.client("s3",region_name="us-east-1")

BUCKET_NAME = "bucket-itops-04261081"

LIMITE_SUBUTILIZADA = 20
LIMITE_ALTA_DENSIDADE = 40


# S3

def listar_arquivos():

    resposta = s3_client.list_objects_v2(
        Bucket=BUCKET_NAME,
        Prefix="trusted/"
    )

    arquivos = []

    for objeto in resposta["Contents"]:

        if objeto["Key"].endswith(".csv"):
            arquivos.append(objeto["Key"])

    return arquivos


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


# Tratamento

def ler_csv(files):

    dados = []

    for arquivo in files:

        file_string = arquivo["Body"].read().decode("UTF-8")

        leitor = csv.DictReader(
            StringIO(file_string)
        )

        for linha in leitor:
            dados.append(linha)

    return dados


def converter_dados(dados):

    for linha in dados:

        linha["active_conn_antena"] = int(
            linha["active_conn_antena"]
        )

    return dados


# Regras de negócio

def gerar_gold_utilizacao(dados):

    for linha in dados:

        linha["active_conn_antena"] = int(
            linha["active_conn_antena"]
        )

        conexoes = linha["active_conn_antena"]

        if conexoes <= LIMITE_SUBUTILIZADA:

            linha["classificacao_utilizacao"] = "SUBUTILIZADA"

        elif conexoes <= LIMITE_ALTA_DENSIDADE:

            linha["classificacao_utilizacao"] = "NORMAL"

        else:

            linha["classificacao_utilizacao"] = "ALTA_DENSIDADE"

    arquivo_csv = StringIO()

    campos = [
        "timestamp",
        "active_conn_antena",
        "classificacao_utilizacao"
    ]

    escritor = csv.DictWriter(
        arquivo_csv,
        fieldnames=campos
    )

    escritor.writeheader()

    for linha in dados:

        linha_gold = {
            "timestamp": linha["timestamp"],
            "active_conn_antena": linha["active_conn_antena"],
            "classificacao_utilizacao": linha["classificacao_utilizacao"]
        }

        escritor.writerow(linha_gold)

    nome_arquivo = datetime.now().strftime(
        "%Y-%m-%d_%H-%M"
    )

    nome_arquivo += "_utilizacao_antenas.csv"

    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key="client/utilizacao_antenas/" + nome_arquivo,
        Body=arquivo_csv.getvalue()
    )

    print(
        f"Gold de utilização enviado: {nome_arquivo}"
    )


def gerar_gold_hardware(dados):

    arquivo_csv = StringIO()

    campos = [
        "timestamp",
        "cpu_antena",
        "ram_usage_antena",
        "status_cpu",
        "status_ram"
    ]

    escritor = csv.DictWriter(
        arquivo_csv,
        fieldnames=campos
    )

    escritor.writeheader()

    for linha in dados:

        linha_gold = {
            "timestamp": linha["timestamp"],
            "cpu_antena": linha["cpu_antena"],
            "ram_usage_antena": linha["ram_usage_antena"],
            "status_cpu": linha["status_cpu"],
            "status_ram": linha["status_ram"]
        }

        escritor.writerow(linha_gold)

    nome_arquivo = datetime.now().strftime(
        "%Y-%m-%d_%H-%M"
    )

    nome_arquivo += "_hardware.csv"

    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key="client/hardware/" + nome_arquivo,
        Body=arquivo_csv.getvalue()
    )

    print(
        f"Gold de hardware enviado: {nome_arquivo}"
    )    


def gerar_gold_seguranca(dados):

    arquivo_csv = StringIO()

    campos = [
        "timestamp",
        "dropped_packets_firewall",
        "top_blocked_ip_firewall"
    ]

    escritor = csv.DictWriter(
        arquivo_csv,
        fieldnames=campos
    )

    escritor.writeheader()

    for linha in dados:

        linha_gold = {
            "timestamp": linha["timestamp"],
            "dropped_packets_firewall": linha["dropped_packets_firewall"],
            "top_blocked_ip_firewall": linha["top_blocked_ip_firewall"]
        }

        escritor.writerow(linha_gold)

    nome_arquivo = datetime.now().strftime(
        "%Y-%m-%d_%H-%M"
    )

    nome_arquivo += "_seguranca.csv"

    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key="client/seguranca/" + nome_arquivo,
        Body=arquivo_csv.getvalue()
    )

    print(
        f"Gold de segurança enviado: {nome_arquivo}"
    )


def gerar_gold_trafego(dados):

    arquivo_csv = StringIO()

    campos = [
        "timestamp",
        "throughput_mbps",
        "diferenca_bytes_wan"
    ]

    escritor = csv.DictWriter(
        arquivo_csv,
        fieldnames=campos
    )

    escritor.writeheader()

    for linha in dados:

        linha_gold = {
            "timestamp": linha["timestamp"],
            "throughput_mbps": linha["throughput_mbps"],
            "diferenca_bytes_wan": linha["diferenca_bytes_wan"]
        }

        escritor.writerow(linha_gold)

    nome_arquivo = datetime.now().strftime(
        "%Y-%m-%d_%H-%M"
    )

    nome_arquivo += "_trafego.csv"

    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key="client/trafego/" + nome_arquivo,
        Body=arquivo_csv.getvalue()
    )

    print(
        f"Gold de tráfego enviado: {nome_arquivo}"
    )


def main():

    arquivos = listar_arquivos()

    files = baixar_arquivos(arquivos)

    dados = ler_csv(files)

    gerar_gold_utilizacao(dados)
    gerar_gold_hardware(dados)
    gerar_gold_seguranca(dados)
    gerar_gold_trafego(dados)


main()