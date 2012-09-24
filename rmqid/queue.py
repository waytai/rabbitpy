"""
Queue is a class that encompasses and returns the methods of the
Specification.Queue class

"""
import logging
from pamqp import specification

from rmqid import base

LOGGER = logging.getLogger(__name__)


class Queue(base.AMQPClass):
    """Queue class that with methods that return the specification class
    method frames.

    """
    def __init__(self, channel, name, passive=False, durable=True,
                 exclusive=False, auto_delete=False):
        """Create a new instance of the queue object.

        :param rmqid.channel.Channel: The channel object to work with
        :param str name: The name of the queue
        :param bool passive: Do not create exchange
        :param bool durable: Request a durable exchange
        :param bool auto_delete: Automatically delete when not in use

        """
        super(Queue, self).__init__(channel, name)
        self._consuming = False
        self._consumer_tag = 'rmqid.%s' % id(self)
        self._passive = passive
        self._durable = durable
        self._exclusive = exclusive
        self._auto_delete = auto_delete

    def bind(self, exchange, routing_key=None):
        """Bind the queue to the specified exchange or routing key.
        If routing key is None, use the queue name.

        :param str | rmqid.base.AMQPClass exchange: The exchange to bind to
        :param str routing_key: The routing key to use

        """
        if isinstance(exchange, base.AMQPClass):
            exchange = exchange.name
        self.rpc(specification.Queue.Bind(queue=self.name,
                                          exchange=exchange,
                                          routing_key=routing_key or self.name))

    def declare(self):
        """Declare the queue"""
        self.rpc(specification.Queue.Declare(queue=self.name,
                                             durable=self._durable,
                                             passive=self._passive,
                                             exclusive=self._exclusive,
                                             auto_delete=self._auto_delete))

    def delete(self, if_unused=False, if_empty=False):
        """Delete the queue

        :param bool if_unused: Delete only if unused
        :param bool if_empty: Delete only if empty

        """
        self.rpc(specification.Queue.Delete(queue=self.name,
                                            if_unused=if_unused,
                                            if_empty=if_empty))

    def unbind(self, exchange, routing_key=None):
        """Unbind queue from the specified exchange where it is bound the
        routing key. If routing key is None, use the queue name.

        :param str | rmqid.base.AMQPClass exchange: Exchange to unbind from
        :param str routing_key: The routing key that binds them

        """
        if isinstance(exchange, base.AMQPClass):
            exchange = exchange.name
        self.rpc(specification.Queue.Bind(queue=self.name,
                                          exchange=exchange,
                                          routing_key=routing_key or self.name))

    def cancel(self):
        """Cancel consuming messages from the RabbitMQ broker"""
        self.rpc(specification.Basic.Cancel(consumer_tag=self._consumer_tag))
        self._consuming = False

    def consume(self):
        """Generator

        """
        self.rpc(specification.Basic.Consume(queue=self.name,
                                             consumer_tag=self._consumer_tag))
        self._consuming = True

        # Block until a message is received
        while self._consuming:
            value = self.channel.get_message()
            if value:
                yield value


    def get(self, no_ack=False):
        """Return the results of a Basic.Get

        :param bool no_ack: Broker should not expect a Basic.Ack,
                            Basic.Reject or Basic.Nack
        :rtype: rmqid.message.Message

        """
        return self.rpc(specification.Basic.Get(queue=self.name, no_ack=no_ack))
