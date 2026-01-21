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