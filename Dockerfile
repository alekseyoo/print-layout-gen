FROM python:3.11-slim

# Step 2: Install git, which is needed to clone the repository
RUN apt-get update && apt-get install -y git

# Step 3: Set the working directory inside the container
WORKDIR /app

# Step 4: Clone the public repository from GitHub into the working directory
RUN git clone https://github.com/alekseyoo/print-layout-gen.git .

# Step 5: Install the Python dependencies listed in the repository's requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Step 6: Expose the port the Flask app runs on internally
EXPOSE 5000

# Step 7: Define the command to run the application
CMD ["flask", "run", "--host=0.0.0.0"]