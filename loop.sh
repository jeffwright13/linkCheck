#!/bin/bash
for i in `seq 1 10`;
do
        echo $i
        ./linkCheck <ftp_ip> <ftp_user> <ftp_pwd> no_modem
done
