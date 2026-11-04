# Two stages: `test` (host code + mock dongle, fast) and `fw` (Zephyr/ZMK-style firmware build, heavy).
FROM python:3.12-slim AS test
WORKDIR /work
RUN pip install --no-cache-dir pytest
COPY host/ host/
COPY tests/ tests/
ENV PYTHONPATH=/work/host
CMD ["pytest", "-q", "tests"]

# Firmware build (untested scaffold): `docker build --target fw -t dongle-fw .`
# then `docker run --rm -v "%cd%/firmware:/fw" -v "%cd%/out:/out" dongle-fw`
FROM zephyrprojectrtos/ci:latest AS fw
WORKDIR /fw
CMD ["bash", "-lc", "west build -p -b nice_nano_v2 /fw -d /out/build && cp /out/build/zephyr/zephyr.uf2 /out/dongle.uf2"]
