import logging
import os
from StringIO import StringIO
from socket import socket, AF_INET, SOCK_STREAM, gaierror, error, timeout

from paramiko import RSAKey, Transport, SSHException
from paramiko.ssh_exception import SSHException
from paramiko.ssh_exception import AuthenticationException
from paramiko.ssh_exception import BadAuthenticationType

from cthulhubot.err import CommunicationError

logger = logging.getLogger("cthulhubot")

class Computer(object):
    def __init__(self, host, user=None, key=None):
        super(Computer, self).__init__()

        self.host = host
        self.user = user
        self.key = key
        self.port = 22

    def connect(self, transport=Transport):
        """
        Connect to remote side. raise CommunicationError on problems
        """
        try:
            key = RSAKey.from_private_key(StringIO(self.key))
        except SSHException:
            raise CommunicationError("Bad RSA key!")

        sock = socket(AF_INET, SOCK_STREAM)
        try:
            sock.connect((self.host, self.port))
        except (error, gaierror, timeout), e:
            raise CommunicationError(e)

        self.transport = transport(sock)
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

    def get_command_return_status(self, command):
        channel = self.transport.open_session()
        channel.exec_command(command)
        rc = channel.recv_exit_status()
        channel.close()
        return rc

    def build_directory_exists(self, directory):
        return self.get_command_return_status("test -d %s" % directory) == 0

    def builder_running(self, directory):
        pid_file = os.path.join(directory, 'twistd.pid')
        cmd = "test -f \"%(pid)s\" && test -d /proc/`cat \"%(pid)s\"`" % {'pid  ' : pid_file}
        return self.get_command_return_status(cmd) == 0

    def disconnect(self):
        self.transport.close()
