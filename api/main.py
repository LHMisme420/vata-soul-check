from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import proofs, batches, metrics

app = FastAPI(
    title="VATA API",
    description="Verification of Authentic Thought Architecture - ZK Proof Registry",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(proofs.router, prefix="/proofs", tags=["Proofs"])
app.include_router(batches.router, prefix="/batches", tags=["Batches"])
app.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])

@app.get("/")
def root():
    return {
        "system": "VATA",
        "version": "1.0.0",
        "status": "ONLINE",
        "protocol": "groth16",
        "curve": "bn128"
    }
