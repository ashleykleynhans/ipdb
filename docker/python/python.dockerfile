# Source Image
FROM python:3.8.1

WORKDIR /app
ADD ./ /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8000 and start API
EXPOSE 8000
CMD [ "python", "./api.py" ]
