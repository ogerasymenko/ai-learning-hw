# Kafka basics

- A topic is split into partitions; order is guaranteed only inside one partition.
- Producers choose the partition by key (same key -> same partition).
- Messages are kept for the retention period (default 7 days), not until consumed.
- Replication factor 3 and `min.insync.replicas=2` survive the loss of one broker.
