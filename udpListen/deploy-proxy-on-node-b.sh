sysctl -w net.ipv4.ip_forward=1
iptables -t mangle -A PREROUTING -p udp --source 10.0.0.1 --destination 10.0.1.3 -j TPROXY --on-port 8080 --tproxy-mark 1
iptables -t mangle -A PREROUTING -p udp --source 10.0.1.3 --destination 10.0.0.1 -j TPROXY --on-port 8080 --tproxy-mark 1

ip rule add fwmark 1 lookup 101
ip route add local 0.0.0.0/0 dev lo table 101

iptables -t nat -A POSTROUTING -j MASQUERADE
