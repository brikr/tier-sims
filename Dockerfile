FROM simulationcraftorg/simc:latest

# Install Python and pip
RUN apk add --no-cache python3 py3-pip

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy application files
COPY . .

# Ensure the docs directory exists
RUN mkdir -p /app/docs

ENTRYPOINT ["sh", "-c", "python3 -u main.py && python3 -u generate_site.py"]
