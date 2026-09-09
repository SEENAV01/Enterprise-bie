import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from envelope import event_envelope,valid
from topic import topic,active
from subscription import subscription
from ordering import ordering,ordered
from delivery import delivery_guarantee,retryable
from retry import retry_policy,allowed
from dead_letter import dead_letter,traceable
from deduplication import deduplication,matches
from consumer import consumer
from ack import acknowledgement,acknowledged

def test_event_topic_subscription():
 assert valid(event_envelope("e","type",{}))
 assert active(topic("t","events"))
 assert subscription("s","t")["status"]=="ACTIVE"

def test_delivery_retry_dlq_dedup():
 assert ordered(ordering("PARTITION"))
 assert retryable(delivery_guarantee("AT_LEAST_ONCE"))
 assert allowed(retry_policy(3),2)
 assert traceable(dead_letter("t","failure","e"))
 assert matches(deduplication("e"),"e")

def test_consumer_ack():
 assert consumer("c","g")["status"]=="ACTIVE"
 assert acknowledged(acknowledgement("e","c"))
