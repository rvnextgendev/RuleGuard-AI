FROM python:3.11-slim
WORKDIR /workspace
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONPATH=/workspace/app
CMD ["streamlit","run","app/ui.py","--server.address=0.0.0.0"]
