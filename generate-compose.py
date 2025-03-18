import sys

SKELETON = """
name: tp0
services:
"""

SERVER = """
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ./server/config.ini:/config.ini 
    networks:
      - testing_net
"""

NETWORKS = """
networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
"""

def create_compose(yaml_file, client_amnt):
    compose_str = SKELETON + SERVER
    
    for i in range(1, client_amnt + 1):
        compose_str += f"""
  client{i}:
    container_name: client{i}
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID={i}
      - CLI_NOMBRE=Francisco
      - CLI_APELLIDO=Juarez
      - CLI_DOCUMENTO=12345678
      - CLI_NACIMIENTO=2000-11-11
      - CLI_NUMERO=7575
    volumes:
      - ./client/config.yaml:/config.yaml
    networks:
      - testing_net
    depends_on:
      - server
"""
    
    compose_str += NETWORKS
    
    with open(yaml_file, "w") as file:
        file.write(compose_str)

    return

def main():
    if len(sys.argv) != 3:
        print("Cantidad de parametros incorrecta, deben ser: <archivo_yaml> <cantidad_clientes>")
        sys.exit(1)

    yaml_file = sys.argv[1]
    try:
        client_amnt = int(sys.argv[2])
        if client_amnt < 0:
            raise ValueError
    except ValueError:
        print("Error: La cantidad de clientes debe ser un número mayor a 0.")
        sys.exit(1)

    create_compose(yaml_file, client_amnt)

if __name__ == "__main__":
    main()