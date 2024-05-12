# /etc/iproute2/rt_tables
# 101 table1
# 102 table2

ip route add default via 192.168.134.96 dev enp0s8 table table1
ip route add default via 192.168.0.1 dev enp0s9 table table2

ip rule add from 192.168.134.12 table table1
ip rule add from 192.168.0.106 table table2
