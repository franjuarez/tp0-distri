#!/bin/bash
echo "Nombre del archivo de salida: $1"
echo "Cantidad de clientes a generar: $2"
python3 generate-compose.py $1 $2