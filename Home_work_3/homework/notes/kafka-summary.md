# Kafka summary

## Topics, partitions, and durability
- Topics are split into partitions. Ordering is guaranteed only within a single partition.
- Producers can choose partitions by key; messages with the same key go to the same partition.
- Messages are retained for the configured retention period (7 days by default), not until they are consumed.
- A replication factor of 3 with `min.insync.replicas=2` can survive the loss of one broker.

## Consumer groups
- Consumers in a group share a topic's partitions, with each partition assigned to one consumer in the group.
- If there are more consumers than partitions, some consumers remain idle.
- Offsets are committed per group, so separate groups can read the same topic independently.
- Consumer lag is the latest offset minus the committed offset. Alert if it continues to grow for several minutes.
- Rebalances pause consumption; cooperative-sticky assignment can shorten them.
