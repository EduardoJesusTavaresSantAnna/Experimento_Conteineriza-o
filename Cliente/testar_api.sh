#!/bin/bash
# Para o script se uma chamada que deveria funcionar falhar.
set -e

# Confere o servidor; as tentativas dão tempo para ele iniciar.
curl --fail --retry 5 --retry-connrefused --retry-delay 1 http://127.0.0.1:8000/health
echo

# Pede o fechamento do dia seguinte ao último dia usado no treino.
curl --fail -X POST http://127.0.0.1:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{}'
echo
