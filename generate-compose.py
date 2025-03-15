import yaml
import sys

def create_compose(yaml_file, client_amnt):
    skeleton = {
        "name": "tp0"
    }
    networks = {
        "networks":{
            "testing_net": {
            "ipam": {
                "driver": "default",
                "config": [{"subnet": "172.25.125.0/24"}],
            }
        }
    }
    }
    server_config = {
            "container_name": "server",
            "image": "server:latest",
            "entrypoint": "python3 /main.py",
            "environment": ["PYTHONUNBUFFERED=1","LOGGING_LEVEL=DEBUG"],
            "networks": ["testing_net"],
    }
    services = { "services": {
        "server": server_config
        }}

    for i in range(client_amnt):
        base_client_data = {
            "container_name": "client1",
            "image": "client:latest",
            "entrypoint": "/client",
            "environment": ["CLI_ID=" + str(i+1), "CLI_LOG_LEVEL=DEBUG"],
            "networks": ["testing_net"],
            "depends_on": ["server"]
        }
        services["services"]["client" + str(i+1)] = base_client_data

    with open(yaml_file, "w") as file:
        yaml.dump(skeleton, file, default_flow_style=False)
        yaml.dump(services, file, default_flow_style=False)
        yaml.dump(networks, file, default_flow_style=False)

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