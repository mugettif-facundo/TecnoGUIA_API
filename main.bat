from fastapi import FastAPI

app = FastAPI(title="API de TecnoGUIA")


@app.get("/")
def inicio():
    return {
        "proyecto": "TecnoGUIA",
        "mensaje": "Mi primera API está funcionando"
    }