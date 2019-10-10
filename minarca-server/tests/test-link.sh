#!/bin/bash
# Integration test to verify if the server accept link from minarca-client.
#
# Copyright (C) 2019 Patrik Dufresne Service Logiciel inc. All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
set -e
set -x

# Default variables
MINARCA_DEB_FILE=${MINARCA_DEB_FILE:-minarca-client_latest_all.deb}
MINARCA_REMOTE_URL=${MINARCA_REMOTE_URL:-https://sestican.patrikdufresne.com}
MINARCA_USERNAME=${MINARCA_USERNAME:-admin}
MINARCA_PASSWORD=${MINARCA_PASSWORD:-admin123}
MINARCA_REPOSITORYNAME=${MINARCA_REPOSITORYNAME:-test}


# Install minarca-client
apt update && apt install -y wget
wget -O $MINARCA_DEB_FILE http://www.patrikdufresne.com/archive/minarca/$MINARCA_DEB_FILE
apt install -y ./$MINARCA_DEB_FILE

# Add PDSL inc certificate
cat <<EOD > /usr/local/share/ca-certificates/root-ca.patrikdufresne.com.crt
-----BEGIN CERTIFICATE-----
MIIFIDCCAwigAwIBAgIQCYygTzogL+sPWi/1cBaGUzANBgkqhkiG9w0BAQsFADAq
MSgwJgYDVQQKDB9QRFNMIGluYy4gQ2VydGlmaWNhdGUgQXV0aG9yaXR5MB4XDTE3
MDIxOTEzNTgzMloXDTI5MDIxNjEzNTgzMlowKjEoMCYGA1UECgwfUERTTCBpbmMu
IENlcnRpZmljYXRlIEF1dGhvcml0eTCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCC
AgoCggIBAKvNpduMYjwXhPNxZyiiD1e9GgjYyW6PSKcewHVVv0VfSjU7mZ/qQ+gz
jLlwiqX+SCZL7tr5rlZlIBlg3HTCIcfZMXJdAfZH17/fqQL1YQJyZRBs9BAFisnA
bEaXOMpKZhQe++ec9XgSk8i0moE9y9KRoKvh+S3GyODZixlozi/qfV12An2fG2An
tG70wUYWgJTRN31djQsZAssYXbNglWERv5b5zXd4IMi93uRowXqh56xlI1Lat0ct
2pH7MS0DGr0aWqv7qmH3dn3Pqsi95Mo+bnHn4JQrH5M9SxGtIOWLDwBQlPzuiSq/
aDFFp9GbzYMWLnt3O9kFKzI28krSbGjsXWDHL+izKCdCLmrjeEfs0OnL03mMYHQu
joQhEFrm5pgnMQBGGuMHLgkKwcgNl4xjAK67PlIALm5BDBNO6PM+Zkhbac7E2Ar8
qw8FV3/kq4b9fJwhlqgl37cUVRi2sAuW9HGXOl0o9MsAWKeot5A60zb0iEmnNa8w
lFP9KS2ggdN5hjoRq3Y4ZSzrDoo99DxuJ8oXrFcIpf8w+65kEUd413/iUpUJNliz
sl8nV76P/TjV1I6/5dDFYdqtJJ2ncccwd/r3lKlWXbVC/vjTY4em4QRE7w1CI4Ar
OX0SBXq7YTI4C4oS654XYtrCUA/1F+GaCHtIaNLjAjlSFvump0HpAgMBAAGjQjBA
MA8GA1UdEwEB/wQFMAMBAf8wDgYDVR0PAQH/BAQDAgEGMB0GA1UdDgQWBBRR5Xxv
DHQFaitYA0E5E0LxjXVfITANBgkqhkiG9w0BAQsFAAOCAgEAch2GRtEdPNqMzzJg
JxRzwGedDZ4JZl/we3AOpCYMwqUYIKDmJ/ZRSSJSOE6NAXM/IVg9tFAdnKdef35V
pPk1Xrx91hUH/I8Qx7RhD1m/N9SvF2P7VlDrM19uN4YnTFmwANB8Ei8sx9b8pJIS
CmR4wB3igZ2Zzu/ueP4cywfGyx1Uqs59hK8ts4cCYu6o8yUyVhQck92Rf2Du9eRT
W8oQIC8QUi9VmDPqCt9mFw8qa0UAsGHIKQc9C92vMuaXnTi4SHpT7nTIEr29Lprj
8m99JXP6LGDHzY9NshJkfWJsyyGIXOl+c/Fow/l0SMG3SJNkPKYwS88FDbMjECFj
M2elVERccLW80EKKOevM9O/i4f6qgF8JjcjaCuNUq/I454lIao/iwLNzYqsID3KS
IUBOat+4rFzzI/EPE/OJ/rA26CoUIRrJGxuSDWqIEO4Pm2+1KGd9pumgqYWd4c16
gHf4G9mXuQ2O5aDfhXldhDkn32s6glZbI6+eBmUZ4PzOMhMcgzaV/iByCXwQ+hRr
c6wzFBZFnUjmVqs6KtlUua541SYEmaQMVZtL3GgJ0anO2vkWoRFcfVcBnkFuT8/q
X5s3ITLM55UuBxaJKoScjzBcp0BztPHRxej62/mJKFGQfbzI4bQWCKE10nU4p4Cq
C8ICepn1o6tfVN/8y9OejsKdocw=
-----END CERTIFICATE-----
EOD
update-ca-certificates

# Link minarca
/opt/minarca/bin/minarca link --remoteurl $MINARCA_REMOTE_URL --username $MINARCA_USERNAME --password $MINARCA_PASSWORD --name $MINARCA_REPOSITORYNAME
