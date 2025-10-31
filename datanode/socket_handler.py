from shared.commons import *

sock = create_socket("0.0.0.0", 5001)
sock.listen()


import sys
print("PYTHONPATH:", sys.path)
