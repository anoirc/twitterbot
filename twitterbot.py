#!/usr/bin/python
# coding=utf-8
# pip install tweepy ja twisted tai ei toimi
# aseta nickname, api-avaimet (https://apps.twitter.com/), twitter-user (toiseksi viimeisellä rivillä) ja irc-serveri (viimeisellä rivillä)
# käyttö: !t viesti
import sys, tweepy, time

from twisted.internet import defer, endpoints, protocol, reactor, task
from twisted.words.protocols import irc
from twisted.python import log

consumer_key = "*"
consumer_secret = "*"
access_token = "*"
access_token_secret = "*"

class MyFirstIRCProtocol(irc.IRCClient):
    nickname = 'botin_nimi'

    def __init__(self):
        self.deferred = defer.Deferred()
        self.lasttime = 0

    def connectionLost(self, reason):
        self.deferred.errback(reason)

    def signedOn(self):
        # This is called once the server has acknowledged that we sent
        # both NICK and USER.
        for channel in self.factory.channels:
            self.join(channel)

    # Obviously, called when a PRIVMSG is received.
    def privmsg(self, user, channel, message):
        nick, _, host = user.partition('!')
        message = message.strip()
        if not message.startswith('!'):  # not a trigger command
            return  # so do nothing
        command, sep, rest = message.lstrip('!').partition(' ')
        # Get the function corresponding to the command given.
        func = getattr(self, 'command_' + command, None)
        # Or, if there was no function, ignore the message.
        currenttime = int(time.time())
        # muokkaa tämä if-lause jos haluat muuttaa cooldown-aikaa tai läpipääseviä viestejä
        if func is None or (currenttime-self.lasttime < 60):
            return "alle 60 sekuntia"
        # maybeDeferred will always return a Deferred. It calls func(rest), and
        # if that returned a Deferred, return that. Otherwise, return the
        # return value of the function wrapped in
        # twisted.internet.defer.succeed. If an exception was raised, wrap the
        # traceback in twisted.internet.defer.fail and return that.
        d = defer.maybeDeferred(func, rest)
        # Add callbacks to deal with whatever the command results are.
        # If the command gives error, the _show_error callback will turn the
        # error into a terse message first:
        d.addErrback(self._showError)
        # Whatever is returned is sent back as a reply:
        if channel == self.nickname:
            # When channel == self.nickname, the message was sent to the bot
            # directly and not to a channel. So we will answer directly too:
            d.addCallback(self._sendMessage, nick)
            self.lasttime = int(time.time())
        else:
            # Otherwise, send the answer to the channel, and use the nick
            # as addressing in the message itself:
            d.addCallback(self._sendMessage, channel, nick)
            self.lasttime = int(time.time())

    def _sendMessage(self, msg, target, nick=None):
        self.msg(target, msg)

    def _showError(self, failure):
        return failure.getErrorMessage()

    def command_t(self, rest):
        if len(rest.decode('utf-8')) > 140:
            return "yli 140 merkkiä"
        else:
            api.update_status(rest)
            url = 'http://twitter.com/statuses/%s' % api.user_timeline(id=user)[0].id
            return url

    def command_tr(self, rest):
        if len(rest.split(' ', 1)[1].decode('utf-8')) > 140:
            return "yli 140 merkkiä"
        else:
            api.update_status(rest.split(' ', 1)[1], in_reply_to_status_id=rest.split(' ', 1)[0])
            url = 'http://twitter.com/statuses/%s' % api.user_timeline(id=user)[0].id
            return url

class MyFirstIRCFactory(protocol.ReconnectingClientFactory):
    protocol = MyFirstIRCProtocol
    channels = ['!7D28Pkuvalauta']


def main(reactor, description):
    endpoint = endpoints.clientFromString(reactor, description)
    factory = MyFirstIRCFactory()
    d = endpoint.connect(factory)
    d.addCallback(lambda protocol: protocol.deferred)
    return d


if __name__ == '__main__':
    log.startLogging(sys.stderr)
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    user = "poimintoja"
    task.react(main, ['tcp:irc.stealth.net:6667'])
