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

# 236 is the smallest documented application-payload budget among fielded
# candidate bearers (goTenna Mesh: the structural bound is 237, a one-byte
# TLV length field's 255 maximum minus the mandatory 18-byte HEAD element,
# and the vendor SDK documents 236 as the supported payload, which is the
# design-to figure). The prior 240 was an arbitrary round number. This
# names a reference budget, not a blessed transport: ZMeta stays
# transport-agnostic.
measure-packets:
	python tools/measure_packet_size.py --file examples/zmeta-profile-L-examples.jsonl --encodings compact --max-bytes 236 --summary-only --validate

release-bundle:
	python release/build_release_bundle.py
