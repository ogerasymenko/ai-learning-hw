# Kafka consumer groups

- Consumers in one group share the partitions of a topic: one partition goes to one consumer.
- More consumers than partitions means idle consumers.
- Offsets are committed per group, so two groups read the same topic independently.
- Consumer lag = latest offset - committed offset; alert when it grows for several minutes.
- A rebalance pauses consumption; use cooperative-sticky assignment to shorten it.
