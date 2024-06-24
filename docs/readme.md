## Run On AWS
### Create an AWS EC2 Instance
![Launch](images/aws/aws-launch-instance.png)

### Run Commands
#### Install docker & docker compose
This section refers to official docker [installation guide](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository).

If you have trouble running the following commands, consider checking the official guide for the latest instructions.

```bash
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```

```bash
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

#### Clone the repository
```bash
git clone git@github.com:socialscan-io/hemera_indexer.git
```

#### Run from source code
```bash
cd hemera_indexer
cd docker-compose
```

Alternatively, you might want to edit environment variables in `docker-compose.yaml`. Please check out [configuration manual](#environment-variables) on how to configure the environment variables.
```bash
vim docker-compose.yaml
```
Now, run this from cmd line to start the indexer.
```bash
sudo docker compose up
```

### Retrieve results
### Read from database

### Read from csv files


# Environment Variables
