#!/usr/bin/env bash
# Activation hook (Unix).

# Point SSL_CERT_DIR at the dir that holds the conda cert bundle; conda-forge's
# openssl otherwise sets it to an empty certs/ subdir.
export SSL_CERT_DIR="${CONDA_PREFIX}/ssl"

# Install MODFLOW 6 on first activation; a fast, offline no-op afterwards. Never
# fails activation. Set MF6_SKIP_AUTOINSTALL to disable (CI runs get-mf6
# explicitly).
if [ -z "${MF6_SKIP_AUTOINSTALL:-}" ]; then
  python "${PIXI_PROJECT_ROOT}/scripts/get_mf6.py" --if-missing --quiet || \
    echo "[get_mf6] WARNING: MODFLOW 6 setup failed; run 'pixi run get-mf6 --force' to retry." >&2
fi
