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

def ensure_connection(method):
    def wrapper(self, *args, **kwargs):
        if not self._connected:
            self.connect()
        return method(self, *args, **kwargs)
    return wrapper


class ComputerAdapter(object):
    def __init__(self, hostname=None, username=None, ssh_key=None, port=None):
        super(ComputerAdapter, self).__init__()

        self.host = hostname
        self.user = username
        self.key = ssh_key
        self.port = port

    def connect(self):
        raise NotImplementedError()

    def disconnect(self):
        raise NotImplementedError()

    @ensure_connection
    def execute_command(self):
        raise NotImplementedError()

    @ensure_connection
    def get_command_return_status(self):
        raise NotImplementedError()

class RemoteComputerAdapter(ComputerAdapter):

    def __init__(self, *args, **kwargs):
        super(RemoteComputerAdapter, self).__init__(*args, **kwargs)

        self._connected = False
        self.transport = None

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

    @ensure_connection
    def get_command_return_status(self, command):
        channel = self.transport.open_session()
        channel.exec_command(' '.join(command))
        rc = channel.recv_exit_status()
        channel.close()
        return rc

class LocalComputerAdapter(ComputerAdapter):
    def connect(self):
        self._connected = True
        return True

    def disconnect(self):
        self._connected = False
        return True

    def get_command_return_status(self, command):
        proc = Popen(' '.join(command), stdout=PIPE, stderr=PIPE, shell=True)
        stdout, stderr = proc.communicate()
        log.debug("Executed local command %s with return code %s. STDOUT: %s STDERR: %s" % (
            str(command), proc.returncode,
            stdout, stderr
        ))
        return proc.returncode
