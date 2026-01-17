.PHONY: gateway-run udp-recv replay-core replay-command validate-examples release-bundle

gateway-run:
	python tools/run_gateway.py --profile H

udp-recv:
	python tools/udp_receiver.py --host 127.0.0.1 --port 5556

replay-core:
	python tools/replay.py --file examples/zmeta-examples-1.0.jsonl --host 127.0.0.1 --port 5555

replay-command:
	python tools/replay.py --file examples/zmeta-command-examples.jsonl --host 127.0.0.1 --port 5555

validate-examples:
	python tools/validate.py --file examples/zmeta-command-examples.jsonl --profile L
	python tools/validate.py --file examples/zmeta-command-examples.jsonl --profile M
	python tools/validate.py --file examples/zmeta-command-examples.jsonl --profile H
	python tools/validate.py --file examples/zmeta-examples-1.0.jsonl --profile H

release-bundle:
	python release/build_release_bundle.py
