#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
infra_root="$(cd "$script_dir/.." && pwd)"
tls_dir="${1:-${TLS_CERT_DIR:-$infra_root/.cache/tls}}"

required_files=(
  ca.crt
  ca.key
  client.crt
  client.key
  server.crt
  server.key
)

certificates_are_valid() {
  local required_file

  for required_file in "${required_files[@]}"; do
    [[ -s "$tls_dir/$required_file" ]] || return 1
  done

  openssl x509 -checkend 2592000 -noout \
    -in "$tls_dir/ca.crt" >/dev/null 2>&1 &&
    openssl x509 -checkend 2592000 -noout \
      -in "$tls_dir/server.crt" >/dev/null 2>&1 &&
    openssl x509 -checkend 2592000 -noout \
      -in "$tls_dir/client.crt" >/dev/null 2>&1 &&
    openssl verify -CAfile "$tls_dir/ca.crt" \
      "$tls_dir/server.crt" "$tls_dir/client.crt" >/dev/null 2>&1
}

command -v openssl >/dev/null || {
  printf 'OpenSSL is required to generate local TLS material.\n' >&2
  exit 1
}

if certificates_are_valid; then
  printf 'Reusing valid local TLS material in %s.\n' "$tls_dir"
  exit 0
fi

mkdir -p "$(dirname "$tls_dir")"
temporary_dir="$(mktemp -d "${tls_dir}.tmp.XXXXXX")"

cleanup() {
  rm -rf "$temporary_dir"
}
trap cleanup EXIT INT TERM

umask 077

openssl genpkey \
  -algorithm RSA \
  -pkeyopt rsa_keygen_bits:2048 \
  -out "$temporary_dir/ca.key" >/dev/null 2>&1
openssl req \
  -x509 \
  -new \
  -sha256 \
  -days 3650 \
  -key "$temporary_dir/ca.key" \
  -subj "/CN=valkey-examples-local-ca" \
  -out "$temporary_dir/ca.crt" >/dev/null 2>&1

openssl genpkey \
  -algorithm RSA \
  -pkeyopt rsa_keygen_bits:2048 \
  -out "$temporary_dir/server.key" >/dev/null 2>&1
openssl req \
  -new \
  -sha256 \
  -key "$temporary_dir/server.key" \
  -subj "/CN=valkey-tls" \
  -out "$temporary_dir/server.csr" >/dev/null 2>&1
openssl x509 \
  -req \
  -sha256 \
  -days 825 \
  -in "$temporary_dir/server.csr" \
  -CA "$temporary_dir/ca.crt" \
  -CAkey "$temporary_dir/ca.key" \
  -CAcreateserial \
  -extfile <(
    printf '%s\n' \
      "basicConstraints=CA:FALSE" \
      "keyUsage=digitalSignature,keyEncipherment" \
      "extendedKeyUsage=serverAuth" \
      "subjectAltName=DNS:valkey-tls,DNS:localhost,IP:127.0.0.1"
  ) \
  -out "$temporary_dir/server.crt" >/dev/null 2>&1

openssl genpkey \
  -algorithm RSA \
  -pkeyopt rsa_keygen_bits:2048 \
  -out "$temporary_dir/client.key" >/dev/null 2>&1
openssl req \
  -new \
  -sha256 \
  -key "$temporary_dir/client.key" \
  -subj "/CN=valkey-examples-client" \
  -out "$temporary_dir/client.csr" >/dev/null 2>&1
openssl x509 \
  -req \
  -sha256 \
  -days 825 \
  -in "$temporary_dir/client.csr" \
  -CA "$temporary_dir/ca.crt" \
  -CAkey "$temporary_dir/ca.key" \
  -CAcreateserial \
  -extfile <(
    printf '%s\n' \
      "basicConstraints=CA:FALSE" \
      "keyUsage=digitalSignature,keyEncipherment" \
      "extendedKeyUsage=clientAuth"
  ) \
  -out "$temporary_dir/client.crt" >/dev/null 2>&1

rm -f \
  "$temporary_dir/ca.srl" \
  "$temporary_dir/client.csr" \
  "$temporary_dir/server.csr"
chmod 600 \
  "$temporary_dir/ca.key" \
  "$temporary_dir/client.key" \
  "$temporary_dir/server.key"
chmod 644 \
  "$temporary_dir/ca.crt" \
  "$temporary_dir/client.crt" \
  "$temporary_dir/server.crt"

openssl verify -CAfile "$temporary_dir/ca.crt" \
  "$temporary_dir/server.crt" "$temporary_dir/client.crt" >/dev/null

rm -rf "$tls_dir"
mv "$temporary_dir" "$tls_dir"
trap - EXIT INT TERM

printf 'Generated local mutual-TLS material in %s.\n' "$tls_dir"
