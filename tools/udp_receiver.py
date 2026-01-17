import argparse
import socket


def parse_args():
    parser = argparse.ArgumentParser(description="Simple UDP receiver")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5556)
    return parser.parse_args()


def main():
    args = parse_args()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.host, args.port))
    print(f"listening on {args.host}:{args.port}")
    while True:
        data, _addr = sock.recvfrom(65535)
        print(data.decode("utf-8", errors="replace"))


if __name__ == "__main__":
    main()
