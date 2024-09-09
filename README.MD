# Instale as dependencias:

## Requisitos
- Python 3.8+
- Ambiente virtual (recomendado)

## Configuração do Ambiente

# Criação do ambiente virtual
python -m venv venv

# Ativação no Windows
.\venv\Scripts\activate

# Ativação no macOS/Linux
source venv/bin/activate

Instalação de dependencias:
```bash
pip install -r requirements.txt
```
 Roda o servidor localmente:
 ```bash
 cd fast_api 
uvicorn main:app --reload
````

