.PHONY: gateway-run gateway-live-test udp-recv replay-core replay-command validate-examples validate-conformance validate-kernel measure-packets release-bundle

gateway-run:
	python tools/run_gateway.py --profile H

gateway-live-test:
	python tools/test_gateway_live.py

udp-recv:
	python tools/udp_receiver.py --host 127.0.0.1 --port 5556

replay-core:
	python tools/replay.py --file examples/zmeta-examples-1.0.jsonl --host 127.0.0.1 --port 5555

replay-command:
	python tools/replay.py --file examples/zmeta-command-examples.jsonl --host 127.0.0.1 --port 5555

validate-examples:
	python tools/validate_examples.py --strict --require-all

validate-conformance:
	python tools/validate_conformance.py --strict

validate-kernel:
	python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness

measure-packets:
	python tools/measure_packet_size.py --file examples/zmeta-profile-L-examples.jsonl --encodings compact --max-bytes 240 --summary-only

release-bundle:
	python release/build_release_bundle.py
