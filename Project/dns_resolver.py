import dns.resolver
import time
from datetime import datetime
import matplotlib.pyplot as plt

print("DNS Resolver & Query Analyzer")

domain = input("\nEnter domain name: ")

print("\nSelect Record Type:")
print("1. A")
print("2. AAAA")
print("3. MX")
print("4. NS")
print("5. CNAME")

choice = input("\nEnter choice number: ")

record_types = {
    "1": "A",
    "2": "AAAA",
    "3": "MX",
    "4": "NS",
    "5": "CNAME"
}

record_type = record_types.get(choice)

if not record_type:
    print("Invalid choice.")
    exit()

dns_servers = {
    "Google DNS": "8.8.8.8",
    "Cloudflare DNS": "1.1.1.1",
    "OpenDNS": "208.67.222.222"
}

results = []

log_file = open(r"C:\Users\DC\Desktop\CN Project\dns_logs.txt", "a")

for server_name, server_ip in dns_servers.items():
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [server_ip]
    resolver.timeout = 5
    resolver.lifetime = 5

    try:
        start_time = time.time()
        answers = resolver.resolve(domain, record_type)
        end_time = time.time()

        response_time = (end_time - start_time) * 1000
        ttl = answers.rrset.ttl

        print(f"\n{server_name} ({server_ip})")
        print("-" * 35)

        answer_list = []

        for answer in answers:
            print("Result:", answer)
            answer_list.append(str(answer))

        print(f"TTL: {ttl} seconds")
        print(f"Response Time: {response_time:.2f} ms")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        log_file.write(
            f"{timestamp}, Domain: {domain}, Record Type: {record_type}, "
            f"DNS Server: {server_name} ({server_ip}), TTL: {ttl}, "
            f"Response Time: {response_time:.2f} ms, Result: {answer_list}\n"
        )

        results.append((server_name, response_time))

    except Exception as e:
        print(f"\n{server_name} ({server_ip})")
        print("Error:", e)

log_file.close()

if results:
    fastest = min(results, key=lambda x: x[1])

    print("\nFastest DNS Server:")
    print(f"{fastest[0]} ({fastest[1]:.2f} ms)")

    server_names = [item[0] for item in results]
    response_times = [item[1] for item in results]

    plt.figure(figsize=(8, 5))
    plt.bar(server_names, response_times)
    plt.xlabel("DNS Servers")
    plt.ylabel("Response Time (ms)")
    plt.title(f"DNS Response Time Comparison for {domain}")
    plt.tight_layout()
    plt.savefig(r"C:\Users\DC\Desktop\CN Project\dns_performance_graph.png")
    plt.show()

print("\nQuery saved in dns_logs.txt")
print("Graph saved as dns_performance_graph.png")