FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    git \
    curl \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    gfortran \
    liblapack-dev \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Clona il repository
RUN git clone https://github.com/firo/basketanalytics.git /app

# Imposta la directory di lavoro
WORKDIR /app

# Crea e attiva un ambiente virtuale
RUN python3 -m venv venv
RUN . ./venv/bin/activate

# Aggiorna pip e installa le dipendenze
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Espone la porta 8501
EXPOSE 8501

# Comando di default quando si esegue il container
CMD ["streamlit", "run", "app.py"]
