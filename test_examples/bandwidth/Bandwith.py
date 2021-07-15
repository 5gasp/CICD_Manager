import paramiko, re
import statistics as stats
import json
import os

host1 = os.getenv('bandwith_host1_ip')
username1 = os.getenv('bandwith_host1_username')
password1 = os.getenv('bandwith_host1_password')

host2 = os.getenv('bandwith_host2_ip')
username2 = os.getenv('bandwith_host2_username')
password2 = os.getenv('bandwith_host2_password')

#test
def bandwith():
    machine1 = paramiko.SSHClient()
    machine1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    machine2 = paramiko.SSHClient()
    machine2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        machine1.connect(hostname=host1, username=username1, password=password1)
        machine2.connect(hostname=host2, username=username2, password=password2)
    except:
        print("[!] Cannot connect to the SSH Server")
        exit()

    # Executing iPerf commands
    machine1.exec_command("iperf3 -s -1")
    stdin, stdout, stderr = machine2.exec_command(f"iperf3 -c {host1} -u --json -t 5")
    iperfResult = stdout.read().decode()
    
    bits_per_second_results = []
    obj = json.loads(iperfResult)
    for iteration_data in (obj['intervals']):
        bits_per_second_results.append(iteration_data["sum"]["bits_per_second"])
    
    if len(bits_per_second_results) > 0: 
        # Calculating the packet loss mean between Sender and Receiver
        mean_bw_bits_per_second = stats.mean(bits_per_second_results)
        if mean_bw_bits_per_second > 800000: 
            return "The bandwidth is bigger than 0.1 MB/sec"
        else:
            return "The bandwidth is lower than 0.1 MB/sec"
        #return f"The mean banddwith is {mean_bw_bits_per_second} bits/sec"
    else:
        return "Not found"


if __name__ == '__main__':

    bandwith()