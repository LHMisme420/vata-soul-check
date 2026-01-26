FROM python:3.12-slim

# Install circom (Rust)
RUN apt-get update && apt-get install -y curl build-essential git
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"
RUN cargo install circom

# Install Node & snarkjs
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs
RUN npm install -g snarkjs

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir gradio

# Pre-download ptau if needed (or mount later)
CMD ["python", "app.py"]
