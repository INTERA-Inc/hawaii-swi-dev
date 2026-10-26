@echo off
REM Activation hook (Windows).

REM Point SSL_CERT_DIR at the dir that holds the conda cert bundle; conda-forge's
REM openssl otherwise sets it to an empty certs\ subdir.
set "SSL_CERT_DIR=%CONDA_PREFIX%\Library\ssl"

REM Install MODFLOW 6 on first activation; a fast, offline no-op afterwards.
REM Never fails activation. Set MF6_SKIP_AUTOINSTALL to disable (CI runs
REM get-mf6 explicitly).
if defined MF6_SKIP_AUTOINSTALL goto :eof
python "%PIXI_PROJECT_ROOT%\scripts\get_mf6.py" --if-missing --quiet || echo [get_mf6] WARNING: MODFLOW 6 setup failed; run "pixi run get-mf6 --force" to retry. 1>&2
