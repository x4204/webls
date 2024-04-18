set -xe

[[ -d demo/empty-dir ]] || mkdir demo/empty-dir
[[ -c demo/char_device ]] || sudo mknod demo/char_device c 246 0
[[ -p demo/fifo ]] || mkfifo demo/fifo
[[ -S demo/unix.sock ]] || python -c 'import socket; socket.socket(socket.AF_UNIX, socket.SOCK_STREAM).bind("demo/unix.sock")'

# rmdir demo/empty-dir
# sudo rm demo/char_device
# rm demo/fifo
# rm demo/unix.sock
