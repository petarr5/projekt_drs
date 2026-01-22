# projekt_drs

Za osposobljavanje projekta, potrebno je prvo inicijalizirati EC2 instance (čvora) na AWS-u u istom VPC-u i subnetu.

Za instance odabrati operacijski sustav Ubuntu i vrstu instance t3.micro. Otvoriti komunikaciju na svim TCP portovima unutar Security grupe.

Pri podešavanju čvorova, razlikujemo podešavanje jednog "Master" čvora i ostalih "Worker" čvorova. Sve naredbe se upisuju u terminal čvora nakon što se povežemo na isti.

**Za postaviti Master čvor**

*sudo apt update*
*sudo apt install -y nfs-kernel-server*

*sudo mkdir -p /mnt/shared*
*sudo chown -R ubuntu:ubuntu /mnt/shared*

*sudo nano /etc/exports*
Dodati: */mnt/shared  *(rw,sync,no_root_squash,no_subtree_check)*
*sudo exportfs -a*
*sudo systemctl restart nfs-kernel-server*
*sudo apt install -y build-essential openmpi-bin libopenmpi-dev*

*ssh-keygen -t rsa -b 4096*
Ovdje potvrđivati bez ikakvog unosa da kreiramo ključ bez lozinke.

*cat ~/.ssh/id_rsa.pub*
Ovdje kopirati ključ koji ćemo zalijepiti u Workere.

**Za postaviti Worker čvor**

*sudo apt update*
*sudo apt install -y nfs-common*

*sudo mkdir -p /mnt/shared*
*sudo mount master_private_ip:/mnt/shared /mnt/shared*

*sudo nano /etc/fstab*
Dodati: *master_private_ip:/mnt/shared  /mnt/shared  nfs  defaults  0  0*

*sudo apt install -y build-essential openmpi-bin libopenmpi-dev*

*nano ~/.ssh/authorized_keys*

Ovdje zaljepiti ključ koji smo kopirali iz Mastera

**NAKON POSTAVLJANJA WORKERA I MASTERA**

Nakon postavljanja čvorova potrebno je se spojiti sa Mastera na svaki Worker.

Na Master čvoru: 

*ssh ubuntu@worker1PublicIP*
Upisati "yes" i pritisnuti Enter.
*exit*

To uraditi za svakog Workera.

Super! Na temelju svega što si poslala, napravio sam **sveobuhvatnu dokumentaciju** za tvoj projekt, organiziranu po logičnim sekcijama: pokretanje servera, baza, API, MPI testiranje, CRUD operacije, load balancing, replikacija, koordinacija, instalacija i provjera stanja. Dodao sam i neke stvari koje obično zaboravimo (Docker, AWS CLI provjere, `start.sh` itd.).

##  Instalacija API i dependency-a


*sudo apt update*
*sudo apt install -y python3-pip*
*pip3 install fastapi uvicorn boto3 --break-system-packages*
*sudo apt install uvicorn*


### Pokretanje API-ja nakon instalacije


*export DYNAMO_HOST=<privatni-ip-mastera>*
*uvicorn api:app --host 0.0.0.0 --port 8081*
*uvicorn api:app --host 0.0.0.0 --port 8082*
*uvicorn api:app --host 0.0.0.0 --port 8083*


## DynamoDB Local – Docker opcija

### Pokretanje lokalnog DynamoDB u Dockeru

*docker run -d -p 8000:8000 amazon/dynamodb-local*
*docker ps*


### Kreiranje tablice


*aws dynamodb create-table \
  --table-name events \
  --attribute-definitions \
      AttributeName=eventId,AttributeType=S \
      AttributeName=version,AttributeType=N \
  --key-schema \
      AttributeName=eventId,KeyType=HASH \
      AttributeName=version,KeyType=RANGE \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --endpoint-url http://localhost:8000 \
  --region us-east-1*


### Provjera tablica


*aws dynamodb list-tables --endpoint-url http://localhost:8000*

##  Pokretanje mastera i servera

Za testiranje i razvoj potrebno je otvoriti **više terminala** na masteru.

### Terminal 1 – Pokretanje servera

*cd /mnt/shared*
*./server*


### Terminal 2 – Pokretanje lokalne DynamoDB baze


*cd /mnt/shared*
*java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb*


### Terminal 3 – Pokretanje API-ja


*uvicorn api:app --host 0.0.0.0 --port 8081*


**Testiranje GET/POST operacija:**
Otvorite preglednik:

http://<javni-ip-mastera>:8081/docs


##  Simulacija konflikta (MPI)

U direktoriju projekta `/mnt/shared/projekt`:

*mpiexec -n 4 -hostfile /home/ubuntu/hosts python3 conflict_sim.py*


##  CRUD operacije (MPI način)

U istom direktoriju `/mnt/shared/projekt`:

**Create**

*mpiexec -n 4 -hostfile /home/ubuntu/hosts python3 mpi_crud.py create e2000*
*mpiexec -n 4 -hostfile /home/ubuntu/hosts python3 mpi_crud.py create e1000*


**Read**

*mpiexec -n 4 -hostfile /home/ubuntu/hosts python3 mpi_crud.py read e1000*


**Update**

*mpiexec -n 4 -hostfile /home/ubuntu/hosts python3 mpi_crud.py update e1000*


**Delete**
*mpiexec -n 4 -hostfile /home/ubuntu/hosts python3 mpi_crud.py delete e1000*

##  Pojedinačne CRUD operacije (bez MPI)

U direktoriju `/mnt/shared`:

*python3 create_event.py*
*python3 read_events.py*
*python3 update_event.py*
*python3 delete_event.py*


### Pokretanje servera lokalno


*uvicorn api:app --reload --host 0.0.0.0 --port 8080*


**Logovi se vide u terminalu.**
###mogu se vidjeti i u datoteci event_service.log
*cat event_service.log*

##  Load balancer i više API instanci

### Pokretanje više API-ja s različitim portovima

*export DYNAMO_HOST=<privatni.ip.mastera>*
*uvicorn api:app --host 0.0.0.0 --port 8081*
*uvicorn api:app --host 0.0.0.0 --port 8082*
*uvicorn api:app --host 0.0.0.0 --port 8083*


### Pokretanje worker-a

*export REPLICAS="http://<privatni-ip-workera-1>:port,http://<privatni-ip-workera-2>:port,http://<privatni-ip-workera-3>:port"*

*python3 worker_api.py*


### Load test i demonstracija tolerancije na greške

*export REPLICAS="http://<privatni-ip-workera-1>:port,http://<privatni-ip-workera-2>:port,http://<privatni-ip-workera-3>:port"*

*python3 load_test.py*
*python3 fault_tolerance_demo.py*


##  Coordinator i replike

### Coordinator


*uvicorn coordinator:app --host 0.0.0.0 --port 8004*


### Replike

*uvicorn replica:app --host 0.0.0.0 --port 8001 &*
*uvicorn replica:app --host 0.0.0.0 --port 8002 &*
*uvicorn replica:app --host 0.0.0.0 --port 8003 &*


### Automatsko pokretanje


*./start.sh*


##  Gašenje procesa


*pkill -f uvicorn*


### Provjera zauzetih portova

*lsof -i :8000*
*lsof -i :8001*
*lsof -i :8002*
*lsof -i :8003*
*lsof -i :8004*


Cleanup:
Gašenje EC2 instanci i brisanje Security Groupe, te lokalno gašenje baze. 

