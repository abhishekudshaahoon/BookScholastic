FROM debian:11-slim
#python:3.11-slim-buster

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    zlib1g-dev \
    python3 \
    sudo \
    curl \
    tdsodbc \
    unixodbc-dev \
    unixodbc

# RUN curl -O https://www.python.org/ftp/python/3.11.1/Python-3.11.1.tgz
# RUN tar -xzf Python-3.11.1.tgz
# WORKDIR Python-3.11.1
# RUN ./configure --enable-optimizations
# RUN make -j $(nproc)
# RUN make altinstall


# ENV PATH="/usr/local/bin:$PATH"

# Install Microsoft SQL Server drivers
RUN curl https://packages.microsoft.com/keys/microsoft.asc | sudo tee /etc/apt/trusted.gpg.d/microsoft.asc
RUN curl https://packages.microsoft.com/config/debian/11/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql18

RUN sudo apt install -y python3-pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy Streamlit application code
WORKDIR /app
COPY . .

# Expose port for Streamlit app
EXPOSE 8000

# Command to run the Streamlit app
#CMD ["streamlit", "run", "chat_app_streamlit.py", "--server.port", "8000"]
CMD ["python", "-m", "streamlit", "run", "chat_app_streamlit.py", "--server.port", "8000", "--server.address", "0.0.0.0"]
