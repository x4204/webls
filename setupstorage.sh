set -xe

[[ -d storage/empty-dir ]] || mkdir storage/empty-dir
[[ -c storage/char_device ]] || mknod storage/char_device c 246 0
[[ -p storage/fifo ]] || mkfifo storage/fifo
[[ -S storage/unix.sock ]] || python -c 'import socket; socket.socket(socket.AF_UNIX, socket.SOCK_STREAM).bind("storage/unix.sock")'

# rmdir storage/empty-dir
# rm storage/char_device
# rm storage/fifo
# rm storage/unix.sock
