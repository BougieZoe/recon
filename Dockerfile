FROM python:3.12-slim

RUN apt-get update -qq && apt-get install -y -qq \
    openssl dnsutils whois curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /recon
COPY . .

ENV PYTHONPATH=/recon
RUN python3 -c "import py_compile; [py_compile.compile(f, doraise=True) for f in __import__('glob').glob('recon/*.py')]"

ENTRYPOINT ["python3", "recon.py"]
CMD ["--help"]
