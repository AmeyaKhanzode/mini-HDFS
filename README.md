# Mini implementation of HDFS

## Read Implementation Structure
![Alt text](./images/read.png)

## Write Implementation Structure
![Alt text](./images/write.png)


When shifting from docker to real machines:
run the below to connect the machines
```
export NAMENODE_HOST=192.168.195.72
export DATANODE1_HOST=192.168.195.221
export DATANODE2_HOST=192.168.195.114
```

on fastapi run this:
export NAMENODE_HOST=192.168.195.72 \
export DATANODE1_HOST=192.168.195.221 \
export DATANODE2_HOST=192.168.195.114 \
uvicorn central_server:app --host 0.0.0.0 --port 8000

on other nodes run the server using sudo -E

pending:
- Automatic Re-replication (Rebuild Logic) - You track dead nodes but don't automatically re-replicate chunks from failed nodes to healthy ones. This is the only partial feature.