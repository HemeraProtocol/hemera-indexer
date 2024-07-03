#### Create an AWS EC2 Instance
1. Navigate to EC2 console
   ![ClickLaunch](images/aws/ec2-portal.png)
2. Launch an AWS Instance
  - Select ubuntu as the operating system
    ![Launch](images/aws/launch-instance.jpg)
  - Select ssh key pair for you to log into the VM later
    ![SSH Key](images/aws/key-pair.png)
  - Change the disk size that fits your need
    ![Disk Size](images/aws/disk-size.png)
  - [TODO] Expose postgres port
  - Click Launch
3. Once the instance is created, ssh into the instance and follow instructions in [Configure Hemera Indexer](#configure-hemera-indexer) section.
