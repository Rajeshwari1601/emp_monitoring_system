import time
from services.heartbeat import send_heartbeat
from services.poller import poll_for_commands

def main():
    print("Employee Agent Started")
    while True:
        send_heartbeat()
        poll_for_commands()
        time.sleep(60)

if __name__ == "__main__":
    main()
