
import boto3
from botocore.exceptions import ClientError
import os
import sys

# Bu scripti calistirmadan once AWS CLI veya ENV degiskenlerini ayarlamalisiniz
# Veya script icine (GUVENSIZ) degil, env'den okuyarak yapacagiz

def verify_email_identity(email_address):
    """
    AWS SES uzerinde bir mail adresini (veya domaini) dogrular.
    Production'da 'no-reply@sirket.com' adresini dogrulamamiz gerekir.
    """
    region = os.getenv('AWS_SES_REGION_NAME', 'eu-central-1')
    aws_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')

    if not aws_key or not aws_secret:
        print("HATA: AWS Credentials bulunamadi. Lutfen .env dosyanizi kontrol edin.")
        return

    client = boto3.client(
        'ses',
        region_name=region,
        aws_access_key_id=aws_key,
        aws_secret_access_key=aws_secret
    )

    try:
        response = client.verify_email_identity(EmailAddress=email_address)
        print(f"Basarili! {email_address} icin dogrulama maili gonderildi.")
        print("Lutfen gelen kutunuzu kontrol edip AWS'den gelen linke tiklayin.")
    except ClientError as e:
        print(f"HATA: {e.response['Error']['Message']}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        email = sys.argv[1]
    else:
        email = input("Dogrulanacak Mail Adresi (orn: no-reply@wfm-pro.com): ")
    
    verify_email_identity(email)
