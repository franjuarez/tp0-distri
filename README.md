# TP0: Docker + Comunicaciones + Concurrencia

## Ejercicio 1

Para hacer el script decidi usar Python, por ende el .sh invoca a una archivo de python que genera el compose con los parametros pasados. Este no usa ninguna libreria, esta hecho con lo basico

## Ejercicio 2

En este punto se pusieron volumenes de Docker en el compose. Estos volumenes linkean los archivos de config presentes en la computadora host con los mismos puestos en el contenedor. De esta forma, como comparten los archivos, cuando se modifique en ela computadora host, docker va a ver los cambios hechos, y viceversa.

## Ejercicio 3

Para este ejercicio, elegí utilizar un script .sh que inicia un contenedor de Docker a partir de su respectivo Dockerfile, lo ejecuta y, al finalizar, lo detiene y lo elimina. El Dockerfile usa Alpine, una imagen mínima de Linux, y ejecuta un script .sh presente en el contenedor, el cual realiza un ping al servidor utilizando netcat. De esta forma el host no tiene que tener instalado netcat, ya que se levanta un container con este y se hace el ping

## Ejercicio 4

Como el servidor está implementado en Python y el cliente en Go, se implementaron dos enfoques diferentes para manejar las señales.

* **Cliente**: Se creó un canal que recibe notificaciones de señales. De esta forma, cada vez que se genere una señal, el canal recibirá un mensaje. Para finalizar el cliente de manera controlada (graceful), se lanza una goroutine al inicio que se mantiene bloqueada leyendo del canal. Cuando esta corrutina detecta un mensaje, invoca el método `close` del Cliente, el cual se encarga de cerrar el socket asociado a la conexión con el servidor (si está activo).

* **Servidor**: Se implementó un manejador de señales dentro de la clase `Servidor`. Al recibir una señal, este manejador invoca una función definida para tal fin. Esta función cierra el servidor llamando al método `stop`, el cual se encarga de cerrar la conexión con el cliente (si está activa) y el socket aceptador del servidor.

## Ejercicio 5

Para este ejercicio se tuvo que crear un protocolo de comunicaion. Se detallara a continuacion.

### Protocolo

El protocolo define la estructura de los mensajes intercambiados entre el cliente y el servidor, asegurando una comunicación eficiente y estructurada en la aplicación.

---

### Mensajes

El protocolo contempla los siguientes tipos de mensajes:

| Mensaje        | Código |
|----------------|--------|
| NEW_BET        | 0      |
| ACK            | 1      |
| NACK           | 3      |

El flujo principal del programa es el siguiente:
1. **El cliente envía** los datos de una/s persona/s para registrar una/s apuesta/s.
2. **El servidor procesa la solicitud y devuelve** una confirmación (ACK) o NACK en caso de que no haya sido exitoso.

---

### Formato de Mensajes

#### 🔹 Formato del mensaje `NEW_BET`
El mensaje `NEW_BET` tiene la siguiente estructura:

| Campo          | Tamaño (bytes) | Descripción                                      |
|---------------|---------------|--------------------------------------------------|
| **Tipo**      | 1             | Tipo de mensaje (`1` = NEW_BET)               |
| **Nro de agencia** | 1             | Numero de la agencia              |
| **Long. Nombre**  | 1         | Longitud en bytes del campo Nombre              |
| **Nombre**    | L1            | Nombre de la persona                            |
| **Long. Apellido** | 1        | Longitud en bytes del campo Apellido            |
| **Apellido**  | L2            | Apellido de la persona                          |
| **Long. Documento** | 1       | Longitud en bytes del campo Documento            |
| **Documento**  | L3            | Documento de la persona                          |
| **Long. Nacim.**  | 1         | Longitud en bytes del campo Nacimiento          |
| **Nacimiento** | L4           | Fecha de nacimiento (AAAA-MM-DD)                |
| **Long. Número**  | 1         | Longitud en bytes del campo Número              |
| **Número**    | L5            | Número de identificación                        |

**Nota:** Se utilizo **1 bytes** para representar las longitudes de cada campo, permitiendo mensajes de hasta **255 bytes** de longitud, lo cual es suficiente para esta aplicación.

---

#### **🔹 Formato del mensaje `ACK`**
El mensaje `ACK` es una simple confirmación del servidor.

#### **🔹 Formato del mensaje `NACK`**
El mensaje `NACK` es un mensjae del servidor que indica que no salio como esperado.

## Ejercicio 6

Se modifico el protocolo, quedando de esta manera: 

| Mensaje        | Código |
|----------------|--------|
| NEW_BET        | 0      |
| ACK            | 1      |
| NEW_BETS_BATCH | 2      |
| NACK           | 3      |

#### 🔹 Formato del mensaje `NEW_BETS_BATCH`

El maximo numero de apuestas por batch esta definido en el config.yaml, pero este numero puede ser que pase los 8Kb maximos por mensaje. Debido a esto, el cliente al ir armando el paquete, chequea el numero de bytes correspondiente, si nota que el paquete se pasa de los 8Kb, procede a mandarlo y crear otro mensaje para terminar de mandar las apuestas. Este algoritmo es escalable a N mensajes de batch.

El mensaje `NEW_BETS_BATCH` tiene la siguiente estructura:

| Campo                | Tamaño (bytes) | Descripción                                      |
|----------------------|--------------- |--------------------------------------------------|
| **Tipo**                 | 1              | Tipo de mensaje (`3` = NEW_BETS_BATCH)           |
| **Nro de agencia**       | 1              | Numero de la agencia                             |
| **Cantidad de apuestas** | 2              | Numero apuestas en el mensaje                    |
| **Bets**                 | Variable       | Secuencia de apuestas en el formato de `NEW_BET` |


Cada apuesta dentro del batch sigue el mismo formato que el mensaje NEW_BET, sin incluir ni el campo Tipo ni Agencia nuevamente.

**Nota:** Se utilizaron **2 bytes** para representar la cantidad de bets, permitiendo mandar hasta **65.535** apuestas, lo cual es suficiente para esta aplicación.

---

## Ejercicio 7

Para este punto se modifico el protocolo para tener en cuenta los nuevos mensajes, queda de esta forma:

| Mensaje         | Código |
|-----------------|--------|
| NEW_BET         | 0      |
| ACK             | 1      |
| NEW_BETS_BATCH  | 2      |
| NACK            | 3      |
| BETS_FINISHED   | 4      |
| ASK_WINNERS     | 5      |
| WAIT_WINNERS    | 6      |
| WINNERS_READY   | 7      |

### 🔹 Flujo de Comunicación

#### **Cliente**
1. Envía todas las apuestas y luego manda `BETS_FINISHED`.
2. Inmediatamente después, envía `ASK_WINNERS` para consultar los ganadores.
3. Dependiendo de la respuesta del servidor:
   - Si recibe `WAIT_WINNERS`, significa que aún no están listos los resultados. En este caso, el cliente espera 1 segundo y vuelve a preguntar.
   - Si recibe `WINNERS_READY`, el servidor envía inmediatamente después la lista de DNIs de los ganadores de la agencia consultada.

#### **Servidor**
1. Recibe apuestas de cada cliente hasta que todos envíen `BETS_FINISHED`.
2. Lleva un registro de qué clientes finalizaron sus envíos.
3. Cuando ha recibido las apuestas de las 5 agencias, realiza el sorteo.
4. Al recibir `ASK_WINNERS`:
   - Responde con `WAIT_WINNERS` si el sorteo aún no se ha realizado.
   - Responde con `WINNERS_READY` y envía la lista de DNIs ganadores cuando los resultados estén disponibles.

---
#### **🔹 Formato del mensaje `BETS_FINISHED`**
El mensaje `BETS_FINISHED` es un mensaje del cliente que notifica al servidor de que este cliente termino de mandar todas las apuestas

Tiene la siguiente estructura:

| Campo                     | Tamaño (bytes) | Descripción                                      |
|---------------------------|--------------- |--------------------------------------------------|
| **Tipo**                  | 1              | Tipo de mensaje `BETS_FINISHED` = 7              |
| **Nro de agencia**        | 1              | Numero de agencia del cliente                    |

#### **🔹 Formato del mensaje `ASK_WINNERS`**
El mensaje `ASK_WINNERS` es un mensaje del cliente que le pregunta al servidor por los ganadores del sorteo

Tiene la siguiente estructura:

| Campo                     | Tamaño (bytes) | Descripción                                      |
|---------------------------|--------------- |--------------------------------------------------|
| **Tipo**                  | 1              | Tipo de mensaje `ASK_WINNERS` = 7              |
| **Nro de agencia**        | 1              | Numero de agencia del cliente                    |


#### **🔹 Formato del mensaje `WAIT_WINNERS`**
El mensaje `WAIT_WINNERS` es un mensaje del servidor que notifica al cliente de que los ganadores todavia no estan listos

#### **🔹 Formato del mensaje `WINNERS_READY`**
El mensaje `WINNERS_READY` es un mensaje del servidor que contiene la lista de DNIs ganadores correspondientes a la agencia del cliente que hizo la consulta

Tiene la siguiente estructura:

| Campo                     | Tamaño (bytes) | Descripción                                      |
|---------------------------|--------------- |--------------------------------------------------|
| **Tipo**                  | 1              | Tipo de mensaje `WINNERS_READY` = 7               |
| **Cantidad de ganadores** | 2              | Numero de ganadores en el mensaje                |
| **Ganadores**             | Variable       | Lista de DNIs de ganadores                       |

Como los DNIs tienen siempre 8 caracteres, el servidor solamente manda la cantidad que hay y luego todos los DNIs seguidos. El cliente sabe que se leen de a 8 caracteres

## Ejercicio 8

Debido a la transición hacia un sistema de procesamiento en paralelo, se optó por utilizar la librería `multiprocessing`. Para adaptarse a esta librería y mejorar el diseño del programa, se separó la lógica del servidor de la de los clientes que atiende. Ahora, el servidor se encarga principalmente de aceptar nuevas conexiones. Al recibir estas conexiones, el servidor crea un proceso por cada cliente, siendo este responsable de intercambiar los mensajes con el cliente.

El procesamiento en paralelo de las solicitudes de los clientes introduce posibles `race conditions`, ya que para procesar las solicitudes es necesario leer o escribir en el archivo donde se almacenan las apuestas, así como en la información relacionada con la lotería. Para abordar el problema relacionado con el archivo de las apuestas, se implementó un `Read-Write Lock`, que permite múltiples lecturas concurrentes, pero bloquea las escrituras cuando hay lectores o escritores activos. Esto se logra mediante una conditional variable que limita el acceso al archivo entre los diferentes procesos.

En cuanto al acceso a la variable compartida de la lotería, se implementó un `Lock` sencillo, el cual asegura que no más de un proceso pueda acceder a esta variable de manera simultánea.

Al ahora ser paralelo, se decidio modificar el protocolo para que el cliente no tenga que abrir conexiones nuevas, y pueda simplemente tener 1 abierta con el servidor y mandar todo por alli.

El unico flujo que cambia es el de `NEW_BETS_BATCH`, ya que ahora, en caso de que maxBatchAmount sea mas pesado que 8Kb, se mandara todas las bets en 1 mensaje pero en paquetes de 8Kb como maximo. Ahora pasa a tener esta estructura:

| Campo                | Tamaño (bytes) | Descripción                                      |
|----------------------|--------------- |--------------------------------------------------|
| **Tipo**                 | 1              | Tipo de mensaje (`3` = NEW_BETS_BATCH)           |
| **Nro de agencia**       | 1              | Numero de la agencia                             |
| **Cant de apuestas** | 2              | Numero apuestas en el mensaje                    |
| **Bets**                 | Variable       | Secuencia de apuestas en el formato de `NEW_BET` |
| **Tipo**                | 1              |  `NEW_BETS_BATCH` si quedan mas apuestas o `EOF` si no hay mas   |

De esta forma el servidor lee la cantidad de apuestas mandadas en el primer mensaje y luego lee si vienen mas apuestas o si terminaron.

Al agregar el mensaje EOF, el protocolo quedaria asi:

| Mensaje         | Código |
|-----------------|--------|
| NEW_BET         | 0      |
| ACK             | 1      |
| NEW_BETS_BATCH  | 2      |
| NACK            | 3      |
| BETS_FINISHED   | 4      |
| ASK_WINNERS     | 5      |
| WAIT_WINNERS    | 6      |
| WINNERS_READY   | 7      |
| EOF             | 8      |

## Consigna

En el presente repositorio se provee un esqueleto básico de cliente/servidor, en donde todas las dependencias del mismo se encuentran encapsuladas en containers. Los alumnos deberán resolver una guía de ejercicios incrementales, teniendo en cuenta las condiciones de entrega descritas al final de este enunciado.

 El cliente (Golang) y el servidor (Python) fueron desarrollados en diferentes lenguajes simplemente para mostrar cómo dos lenguajes de programación pueden convivir en el mismo proyecto con la ayuda de containers, en este caso utilizando [Docker Compose](https://docs.docker.com/compose/).

## Instrucciones de uso
El repositorio cuenta con un **Makefile** que incluye distintos comandos en forma de targets. Los targets se ejecutan mediante la invocación de:  **make \<target\>**. Los target imprescindibles para iniciar y detener el sistema son **docker-compose-up** y **docker-compose-down**, siendo los restantes targets de utilidad para el proceso de depuración.

Los targets disponibles son:

| target  | accion  |
|---|---|
|  `docker-compose-up`  | Inicializa el ambiente de desarrollo. Construye las imágenes del cliente y el servidor, inicializa los recursos a utilizar (volúmenes, redes, etc) e inicia los propios containers. |
| `docker-compose-down`  | Ejecuta `docker-compose stop` para detener los containers asociados al compose y luego  `docker-compose down` para destruir todos los recursos asociados al proyecto que fueron inicializados. Se recomienda ejecutar este comando al finalizar cada ejecución para evitar que el disco de la máquina host se llene de versiones de desarrollo y recursos sin liberar. |
|  `docker-compose-logs` | Permite ver los logs actuales del proyecto. Acompañar con `grep` para lograr ver mensajes de una aplicación específica dentro del compose. |
| `docker-image`  | Construye las imágenes a ser utilizadas tanto en el servidor como en el cliente. Este target es utilizado por **docker-compose-up**, por lo cual se lo puede utilizar para probar nuevos cambios en las imágenes antes de arrancar el proyecto. |
| `build` | Compila la aplicación cliente para ejecución en el _host_ en lugar de en Docker. De este modo la compilación es mucho más veloz, pero requiere contar con todo el entorno de Golang y Python instalados en la máquina _host_. |

### Servidor

Se trata de un "echo server", en donde los mensajes recibidos por el cliente se responden inmediatamente y sin alterar. 

Se ejecutan en bucle las siguientes etapas:

1. Servidor acepta una nueva conexión.
2. Servidor recibe mensaje del cliente y procede a responder el mismo.
3. Servidor desconecta al cliente.
4. Servidor retorna al paso 1.


### Cliente
 se conecta reiteradas veces al servidor y envía mensajes de la siguiente forma:
 
1. Cliente se conecta al servidor.
2. Cliente genera mensaje incremental.
3. Cliente envía mensaje al servidor y espera mensaje de respuesta.
4. Servidor responde al mensaje.
5. Servidor desconecta al cliente.
6. Cliente verifica si aún debe enviar un mensaje y si es así, vuelve al paso 2.

### Ejemplo

Al ejecutar el comando `make docker-compose-up`  y luego  `make docker-compose-logs`, se observan los siguientes logs:

```
client1  | 2024-08-21 22:11:15 INFO     action: config | result: success | client_id: 1 | server_address: server:12345 | loop_amount: 5 | loop_period: 5s | log_level: DEBUG
client1  | 2024-08-21 22:11:15 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°1
server   | 2024-08-21 22:11:14 DEBUG    action: config | result: success | port: 12345 | listen_backlog: 5 | logging_level: DEBUG
server   | 2024-08-21 22:11:14 INFO     action: accept_connections | result: in_progress
server   | 2024-08-21 22:11:15 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:15 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°1
server   | 2024-08-21 22:11:15 INFO     action: accept_connections | result: in_progress
server   | 2024-08-21 22:11:20 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:20 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°2
server   | 2024-08-21 22:11:20 INFO     action: accept_connections | result: in_progress
client1  | 2024-08-21 22:11:20 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°2
server   | 2024-08-21 22:11:25 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:25 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°3
client1  | 2024-08-21 22:11:25 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°3
server   | 2024-08-21 22:11:25 INFO     action: accept_connections | result: in_progress
server   | 2024-08-21 22:11:30 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:30 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°4
server   | 2024-08-21 22:11:30 INFO     action: accept_connections | result: in_progress
client1  | 2024-08-21 22:11:30 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°4
server   | 2024-08-21 22:11:35 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:35 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°5
client1  | 2024-08-21 22:11:35 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°5
server   | 2024-08-21 22:11:35 INFO     action: accept_connections | result: in_progress
client1  | 2024-08-21 22:11:40 INFO     action: loop_finished | result: success | client_id: 1
client1 exited with code 0
```


## Parte 1: Introducción a Docker
En esta primera parte del trabajo práctico se plantean una serie de ejercicios que sirven para introducir las herramientas básicas de Docker que se utilizarán a lo largo de la materia. El entendimiento de las mismas será crucial para el desarrollo de los próximos TPs.

### Ejercicio N°1:
Definir un script de bash `generar-compose.sh` que permita crear una definición de Docker Compose con una cantidad configurable de clientes.  El nombre de los containers deberá seguir el formato propuesto: client1, client2, client3, etc. 

El script deberá ubicarse en la raíz del proyecto y recibirá por parámetro el nombre del archivo de salida y la cantidad de clientes esperados:

`./generar-compose.sh docker-compose-dev.yaml 5`

Considerar que en el contenido del script pueden invocar un subscript de Go o Python:

```
#!/bin/bash
echo "Nombre del archivo de salida: $1"
echo "Cantidad de clientes: $2"
python3 mi-generador.py $1 $2
```

En el archivo de Docker Compose de salida se pueden definir volúmenes, variables de entorno y redes con libertad, pero recordar actualizar este script cuando se modifiquen tales definiciones en los sucesivos ejercicios.

### Ejercicio N°2:
Modificar el cliente y el servidor para lograr que realizar cambios en el archivo de configuración no requiera reconstruír las imágenes de Docker para que los mismos sean efectivos. La configuración a través del archivo correspondiente (`config.ini` y `config.yaml`, dependiendo de la aplicación) debe ser inyectada en el container y persistida por fuera de la imagen (hint: `docker volumes`).


### Ejercicio N°3:
Crear un script de bash `validar-echo-server.sh` que permita verificar el correcto funcionamiento del servidor utilizando el comando `netcat` para interactuar con el mismo. Dado que el servidor es un echo server, se debe enviar un mensaje al servidor y esperar recibir el mismo mensaje enviado.

En caso de que la validación sea exitosa imprimir: `action: test_echo_server | result: success`, de lo contrario imprimir:`action: test_echo_server | result: fail`.

El script deberá ubicarse en la raíz del proyecto. Netcat no debe ser instalado en la máquina _host_ y no se pueden exponer puertos del servidor para realizar la comunicación (hint: `docker network`). `


### Ejercicio N°4:
Modificar servidor y cliente para que ambos sistemas terminen de forma _graceful_ al recibir la signal SIGTERM. Terminar la aplicación de forma _graceful_ implica que todos los _file descriptors_ (entre los que se encuentran archivos, sockets, threads y procesos) deben cerrarse correctamente antes que el thread de la aplicación principal muera. Loguear mensajes en el cierre de cada recurso (hint: Verificar que hace el flag `-t` utilizado en el comando `docker compose down`).

## Parte 2: Repaso de Comunicaciones

Las secciones de repaso del trabajo práctico plantean un caso de uso denominado **Lotería Nacional**. Para la resolución de las mismas deberá utilizarse como base el código fuente provisto en la primera parte, con las modificaciones agregadas en el ejercicio 4.

### Ejercicio N°5:
Modificar la lógica de negocio tanto de los clientes como del servidor para nuestro nuevo caso de uso.

#### Cliente
Emulará a una _agencia de quiniela_ que participa del proyecto. Existen 5 agencias. Deberán recibir como variables de entorno los campos que representan la apuesta de una persona: nombre, apellido, DNI, nacimiento, numero apostado (en adelante 'número'). Ej.: `NOMBRE=Santiago Lionel`, `APELLIDO=Lorca`, `DOCUMENTO=30904465`, `NACIMIENTO=1999-03-17` y `NUMERO=7574` respectivamente.

Los campos deben enviarse al servidor para dejar registro de la apuesta. Al recibir la confirmación del servidor se debe imprimir por log: `action: apuesta_enviada | result: success | dni: ${DNI} | numero: ${NUMERO}`.



#### Servidor
Emulará a la _central de Lotería Nacional_. Deberá recibir los campos de la cada apuesta desde los clientes y almacenar la información mediante la función `store_bet(...)` para control futuro de ganadores. La función `store_bet(...)` es provista por la cátedra y no podrá ser modificada por el alumno.
Al persistir se debe imprimir por log: `action: apuesta_almacenada | result: success | dni: ${DNI} | numero: ${NUMERO}`.

#### Comunicación:
Se deberá implementar un módulo de comunicación entre el cliente y el servidor donde se maneje el envío y la recepción de los paquetes, el cual se espera que contemple:
* Definición de un protocolo para el envío de los mensajes.
* Serialización de los datos.
* Correcta separación de responsabilidades entre modelo de dominio y capa de comunicación.
* Correcto empleo de sockets, incluyendo manejo de errores y evitando los fenómenos conocidos como [_short read y short write_](https://cs61.seas.harvard.edu/site/2018/FileDescriptors/).


### Ejercicio N°6:
Modificar los clientes para que envíen varias apuestas a la vez (modalidad conocida como procesamiento por _chunks_ o _batchs_). 
Los _batchs_ permiten que el cliente registre varias apuestas en una misma consulta, acortando tiempos de transmisión y procesamiento.

La información de cada agencia será simulada por la ingesta de su archivo numerado correspondiente, provisto por la cátedra dentro de `.data/datasets.zip`.
Los archivos deberán ser inyectados en los containers correspondientes y persistido por fuera de la imagen (hint: `docker volumes`), manteniendo la convencion de que el cliente N utilizara el archivo de apuestas `.data/agency-{N}.csv` .

En el servidor, si todas las apuestas del *batch* fueron procesadas correctamente, imprimir por log: `action: apuesta_recibida | result: success | cantidad: ${CANTIDAD_DE_APUESTAS}`. En caso de detectar un error con alguna de las apuestas, debe responder con un código de error a elección e imprimir: `action: apuesta_recibida | result: fail | cantidad: ${CANTIDAD_DE_APUESTAS}`.

La cantidad máxima de apuestas dentro de cada _batch_ debe ser configurable desde config.yaml. Respetar la clave `batch: maxAmount`, pero modificar el valor por defecto de modo tal que los paquetes no excedan los 8kB. 

Por su parte, el servidor deberá responder con éxito solamente si todas las apuestas del _batch_ fueron procesadas correctamente.

### Ejercicio N°7:

Modificar los clientes para que notifiquen al servidor al finalizar con el envío de todas las apuestas y así proceder con el sorteo.
Inmediatamente después de la notificacion, los clientes consultarán la lista de ganadores del sorteo correspondientes a su agencia.
Una vez el cliente obtenga los resultados, deberá imprimir por log: `action: consulta_ganadores | result: success | cant_ganadores: ${CANT}`.

El servidor deberá esperar la notificación de las 5 agencias para considerar que se realizó el sorteo e imprimir por log: `action: sorteo | result: success`.
Luego de este evento, podrá verificar cada apuesta con las funciones `load_bets(...)` y `has_won(...)` y retornar los DNI de los ganadores de la agencia en cuestión. Antes del sorteo no se podrán responder consultas por la lista de ganadores con información parcial.

Las funciones `load_bets(...)` y `has_won(...)` son provistas por la cátedra y no podrán ser modificadas por el alumno.

No es correcto realizar un broadcast de todos los ganadores hacia todas las agencias, se espera que se informen los DNIs ganadores que correspondan a cada una de ellas.

## Parte 3: Repaso de Concurrencia
En este ejercicio es importante considerar los mecanismos de sincronización a utilizar para el correcto funcionamiento de la persistencia.

### Ejercicio N°8:

Modificar el servidor para que permita aceptar conexiones y procesar mensajes en paralelo. En caso de que el alumno implemente el servidor en Python utilizando _multithreading_,  deberán tenerse en cuenta las [limitaciones propias del lenguaje](https://wiki.python.org/moin/GlobalInterpreterLock).

## Condiciones de Entrega
Se espera que los alumnos realicen un _fork_ del presente repositorio para el desarrollo de los ejercicios y que aprovechen el esqueleto provisto tanto (o tan poco) como consideren necesario.

Cada ejercicio deberá resolverse en una rama independiente con nombres siguiendo el formato `ej${Nro de ejercicio}`. Se permite agregar commits en cualquier órden, así como crear una rama a partir de otra, pero al momento de la entrega deberán existir 8 ramas llamadas: ej1, ej2, ..., ej7, ej8.
 (hint: verificar listado de ramas y últimos commits con `git ls-remote`)

Se espera que se redacte una sección del README en donde se indique cómo ejecutar cada ejercicio y se detallen los aspectos más importantes de la solución provista, como ser el protocolo de comunicación implementado (Parte 2) y los mecanismos de sincronización utilizados (Parte 3).

Se proveen [pruebas automáticas](https://github.com/7574-sistemas-distribuidos/tp0-tests) de caja negra. Se exige que la resolución de los ejercicios pase tales pruebas, o en su defecto que las discrepancias sean justificadas y discutidas con los docentes antes del día de la entrega. El incumplimiento de las pruebas es condición de desaprobación, pero su cumplimiento no es suficiente para la aprobación. Respetar las entradas de log planteadas en los ejercicios, pues son las que se chequean en cada uno de los tests.

La corrección personal tendrá en cuenta la calidad del código entregado y casos de error posibles, se manifiesten o no durante la ejecución del trabajo práctico. Se pide a los alumnos leer atentamente y **tener en cuenta** los criterios de corrección informados  [en el campus](https://campusgrado.fi.uba.ar/mod/page/view.php?id=73393).
