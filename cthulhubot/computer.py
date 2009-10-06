from subprocess import Popen, PIPE
import logging
import os
from StringIO import StringIO
from socket import socket, AF_INET, SOCK_STREAM, gaierror, error, timeout

from paramiko import RSAKey, Transport, SSHException
from paramiko.ssh_exception import SSHException
from paramiko.ssh_exception import AuthenticationException
from paramiko.ssh_exception import BadAuthenticationType

from cthulhubot.err import CommunicationError

log = logger = logging.getLogger("cthulhubot")

class Computer(object):

    def __init__(self, host, user=None, key=None, model=None):
        super(Computer, self).__init__()

        port = 22

        if host in ("localhost", "127.0.0.1", "::1"):
            self.adapter = LocalComputerAdapter()
        else:
            self.adapter = RemoteComputerAdapter(host=host, user=user, key=key, port=port)

        self.model = model
        self.host = host
        self._basedir = None

    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError, e:
            if hasattr(self.adapter, name):
                return getattr(self.adapter, name)
            raise

    def __unicode__(self):
        if self.model:
            return self.model.name
        else:
            return u"Unsaved %s" % self.host

    def build_directory_exists(self, directory):
        return self.get_command_return_status(["test", "-d", directory]) == 0

    def get_base_build_directory(self):
        if not self._basedir:
            self._basedir = self.model.basedir

        assert self._basedir is not None

        return self._basedir

    def create_build_directory(self, *args, **kwargs):
        self.assignment.create_build_directory(*args, **kwargs)

class ComputerAdapter(object):
    def __init__(self, host=None, user=None, key=None, port=None):
        super(ComputerAdapter, self).__init__()

        self.host = host
        self.user = user
        self.key = key
        self.port = port

    def connect(self):
        raise NotImplementedError()

    def disconnect(self):
        raise NotImplementedError()

    def execute_command(self):
        raise NotImplementedError()


class RemoteComputerAdapter(ComputerAdapter):
    def connect(self):
        self.transport = None
        try:
            key = RSAKey.from_private_key(StringIO(self.key))
        except SSHException:
            raise CommunicationError("Bad RSA key!")

        sock = socket(AF_INET, SOCK_STREAM)
        try:
            sock.connect((self.host, self.port))
        except (error, gaierror, timeout), e:
            raise CommunicationError(e)

        self.transport = Transport(sock)
        try:
            self.transport.start_client()
            self.transport.auth_publickey(self.user, key)
        except SSHException:
            self.disconnect()
            raise CommunicationError("SSH negotiation failed")
        except (BadAuthenticationType, AuthenticationException), e:
            self.disconnect()
            raise CommunicationError("Authentication failed")



        #TODO: key management
#        key = t.get_remote_server_key()
#        if not keys.has_key(hostname) or not keys[hostname].has_key(key.get_name():
#            logger.warn('Unknown host key')
#        elif not keys[hostname].has_key(key.get_name()):
#            print '*** WARNING: Unknown host key!'
#        elif keys[hostname][key.get_name()] != key:
#            print '*** WARNING: Host key has changed!!!'
#            sys.exit(1)
#        else:
#            print '*** Host key OK.'
#        chan = t.open_session()
#        chan.get_pty()
#        chan.invoke_shell()
#        interactive.interactive_shell(chan)
#        chan.close()

    def disconnect(self):
        if self.transport:
            self.transport.close()

    def get_command_return_status(self, command):
        channel = self.transport.open_session()
        channel.exec_command(' '.join(command))
        rc = channel.recv_exit_status()
        channel.close()
        return rc

class LocalComputerAdapter(ComputerAdapter):
    def connect(self):
        return True

    def disconnect(self):
        return True

    def get_command_return_status(self, command):
        proc = Popen(command, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        log.debug("Executed local command %s with return code %s. STDOUT: %s STDERR: %s" % (
            str(command), proc.returncode,
            stdout, stderr
        ))
        return proc.returncode
