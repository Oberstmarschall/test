#!/bin/bash
set -euxo pipefail

sudo losetup /dev/loop2 /fake_disk.img || true

exec "$@"
