import ctypes

# I do hope this isn't clown nonsense.
# byte_literal = b'58 58 58 58 49 66 20 77 65 20 73 6c 69 63 65 20 74 6f 20 34 20 62 79 74 65 73 2c 20 77 65 20 73 68 6f 75 6c 64 6e 27 74 20 73 65 65 20 74 68 65 20 66 6f 75 72 20 78 27 73 20 61 74 20 74 68 65 20 62 65 67 67 69 6e 67 2e 20 4e 6f 74 20 73 75 72 65 20 77 68 65 72 65 20 69 74 27 6c 6c 20 73 74 6f 70 20 62 75 74 20 74 68 61 74 27 73 20 66 69 6e 65 2e'
# byte_literal = b'XXXXIf we slice to 4 bytes, we shouldnt see the four xs at the begging. Not sure where itll stop but thats fine.'
byte_literal = 'XXXXIf we slice to 4 bytes, we shouldnt see the four xs at the beggining.\0 Not sure where itll stop but thats fine.'.encode('ascii')

string = ctypes.create_string_buffer(byte_literal[4:]).value.decode()
print(byte_literal)
print("-----")
print(string)