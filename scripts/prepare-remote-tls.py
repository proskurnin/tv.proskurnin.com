#!/usr/bin/env python3
"""Create a private local CA and an IP certificate. Never install or trust automatically."""
import argparse,datetime,ipaddress,os,plistlib,secrets,uuid
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID,ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--ip',required=True);args=p.parse_args();ip=ipaddress.ip_address(args.ip)
 if not ip.is_private or ip.version!=4:raise ValueError('Private IPv4 required')
 folder=ROOT/'integrations/remote/private';folder.mkdir(mode=0o700,parents=True,exist_ok=True);os.chmod(folder,0o700)
 def save(name,data):
  path=folder/name
  if path.is_symlink():raise ValueError('Symlink refused')
  fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
  with os.fdopen(fd,'wb') as f:f.write(data)
 now=datetime.datetime.now(datetime.timezone.utc)
 if (folder/'ca-key.pem').exists():
  ca_key=serialization.load_pem_private_key((folder/'ca-key.pem').read_bytes(),None);ca=x509.load_pem_x509_certificate((folder/'ca.pem').read_bytes())
 else:
  ca_key=rsa.generate_private_key(public_exponent=65537,key_size=3072);name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'Proskurnin TV Local Remote CA')]);ca=x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(ca_key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(days=1)).not_valid_after(now+datetime.timedelta(days=1825)).add_extension(x509.BasicConstraints(ca=True,path_length=0),True).add_extension(x509.KeyUsage(False,False,False,False,False,True,True,False,False),True).add_extension(x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()),False).sign(ca_key,hashes.SHA256());save('ca-key.pem',ca_key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()));save('ca.pem',ca.public_bytes(serialization.Encoding.PEM))
 key=rsa.generate_private_key(public_exponent=65537,key_size=2048);cert=x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'Proskurnin TV Remote')])).issuer_name(ca.subject).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(hours=1)).not_valid_after(now+datetime.timedelta(days=365)).add_extension(x509.BasicConstraints(ca=False,path_length=None),True).add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()),False).add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),False).add_extension(x509.SubjectAlternativeName([x509.IPAddress(ip)]),False).add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),False).add_extension(x509.KeyUsage(True,False,True,False,False,False,False,False,False),True).sign(ca_key,hashes.SHA256())
 password=secrets.token_urlsafe(32);encryption=serialization.PrivateFormat.PKCS12.encryption_builder().kdf_rounds(20000).key_cert_algorithm(pkcs12.PBES.PBESv1SHA1And3KeyTripleDESCBC).hmac_hash(hashes.SHA1()).build(password.encode())
 save('remote.p12',pkcs12.serialize_key_and_certificates(b'remote',key,cert,[ca],encryption));save('tls-password',password.encode());save('server.pem',cert.public_bytes(serialization.Encoding.PEM));save('ca.cer',ca.public_bytes(serialization.Encoding.DER))
 profile={'PayloadType':'Configuration','PayloadVersion':1,'PayloadIdentifier':'local.proskurnin.remote.ca','PayloadUUID':str(uuid.uuid4()),'PayloadDisplayName':'Proskurnin TV · локальный пульт','PayloadDescription':'Сертификат для HTTPS-пульта в вашей домашней сети. Не VPN и не прокси.','PayloadContent':[{'PayloadType':'com.apple.security.root','PayloadVersion':1,'PayloadIdentifier':'local.proskurnin.remote.root','PayloadUUID':str(uuid.uuid4()),'PayloadDisplayName':'Proskurnin TV Local Remote CA','PayloadContent':ca.public_bytes(serialization.Encoding.DER)}]};save('remote-ca.mobileconfig',plistlib.dumps(profile));save('fingerprint.txt',(ca.fingerprint(hashes.SHA256()).hex().upper()+'\n').encode());print('HTTPS certificate for',ip,'expires',cert.not_valid_after_utc.isoformat());print('CA SHA256:',ca.fingerprint(hashes.SHA256()).hex().upper())
if __name__=='__main__':main()
