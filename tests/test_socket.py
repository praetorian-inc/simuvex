from __future__ import print_function
from simuvex.s_errors import SimFileError

import nose
import angr
import subprocess
import socket

import os
test_location = str(os.path.dirname(os.path.realpath(__file__)))

def run_sockets(threads):
    for arch in ['x86_64', 'x86']:
        # test_bin = os.path.join(test_location, "../../binaries/tests/{}/socket_test".format(arch))
        test_bin = os.path.join(test_location, "binaries/tests/{}/socket_test".format(arch))
        b = angr.Project(test_bin, load_options={"auto_load_libs":False})

        pg = b.factory.path_group(immutable=False)#, threads=threads)

        # find the end of main
        expected_outputs = { 
            "send case 1 works. ",
            "more data. nope. ",
            "more data. send case 2 works. "
        }

        pg.explore()
        nose.tools.assert_equal(len(pg.deadended), len(expected_outputs))

        # check the outputs
        pipe = subprocess.PIPE
        for f in pg.deadended:
            for socket_fd, recv_send in f.state.posix.sockets.iteritems():
                test_input, test_output = None, None
                try:
                    test_input = f.state.posix.dumps(recv_send.recv_fd)
                except SimFileError as e:
                    if 'no content in' in str(e):
                        pass

                try:
                    test_output = f.state.posix.dumps(recv_send.send_fd)
                except SimFileError as e:
                    if 'no content in' in str(e):
                        pass


                if not test_output:
                    continue

                expected_outputs.remove(test_output)

                # check the output works as expected
                p = subprocess.Popen(test_bin)
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect(('127.0.0.1', 7891))
                client_socket.send(test_input)
                output = client_socket.recv(1024)

        # check that all of the outputs were seen
        nose.tools.assert_equal(len(expected_outputs), 0)

def test_sscanf():
    yield run_sockets, None
    yield run_sockets, 8

if __name__ == "__main__":
    run_sockets(4)
