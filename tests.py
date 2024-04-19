import html5lib
import os
import unittest
import webls

from pathlib import Path
from werkzeug.test import Client


class TestWebls(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.app = webls.app_build(
            development=False,
            root=Path('.').absolute(),
            fs_root=Path('demo').absolute(),
        )
        self.client = Client(self.app)

        self.response = None
        self.body = None

    def parse_body(self, response):
        if response.mimetype == 'text/html':
            return html5lib.parse(
                response.text,
                namespaceHTMLElements=False,
            )
        else:
            raise NotImplementedError(response.mimetype)

    def get(self, path):
        self.response = self.client.get(path)
        self.body = self.parse_body(self.response)

    def assert_status_code(self, status_code):
        actual_status_code = self.response.status_code

        self.assertEqual(status_code, actual_status_code)

    def assert_redirect(self, code, location):
        actual_location = self.response.location

        self.assert_status_code(code)
        self.assertEqual(location, actual_location)

    def assert_title(self, title):
        actual_title = self.body.find('.//title').text

        self.assertEqual(title, actual_title)

    def assert_crumbs(self, *crumbs):
        actual_crumbs = [
            {
                'class': a.get('class'),
                'url': a.get('href'),
                'text': a.find('code').text,
            }
            for a in self.body.findall('.//nav/div[@class="crumbs"]//a')
        ]

        self.assertEqual(list(crumbs), actual_crumbs)

    def assert_dl_btn(self, url):
        a = self.body.find('.//nav//a[@class="dl-btn"]')
        actual_url = a.get('href')

        self.assertEqual(url, actual_url)

    def assert_entries(self, *entries):
        actual_entries = []

        for tr in self.body.findall('.//tr[@class="entry"]'):
            td_mode, td_size, td_name, td_action = tr.findall('./td')
            dl_btn = td_action.find('a')
            entry = {
                'mode': {
                    'text': td_mode.text.strip()
                },
                'size': {
                    'title': td_size.get('title'),
                    'text': td_size.text.strip(),
                },
                'name': {
                    'title': td_name.get('title'),
                    'class': td_name.find('a').get('class'),
                    'href': td_name.find('a').get('href'),
                    'text': ' '.join([
                        text.strip()
                        for text in td_name.itertext()
                    ]).strip(),
                },
                'action': {},
            }

            if dl_btn is not None:
                entry['action'] = {
                    'title': 'download',
                    'href': dl_btn.get('href'),
                    'text': '&#8623;',
                }

            actual_entries.append(entry)

        self.assertEqual(list(entries), actual_entries)

    def assert_message(self, klass, message, path=None, url=None, url_text=None):
        main = self.body.find(f'.//main[@class="{klass}"]')
        actual_message = main.find('./div[@class="message"]').text.strip()
        actual_path = None
        actual_url = None
        actual_url_text = None

        p = main.find('./p[@class="path"]')
        if p is not None:
            actual_path = p.text.strip()

        a = main.find('./a')
        if a is not None:
            actual_url = a.get('href')
            actual_url_text = a.text.strip()

        self.assertEqual(message, actual_message)
        self.assertEqual(path, actual_path)
        self.assertEqual(url, actual_url)
        self.assertEqual(url_text, actual_url_text)

    def assert_warning(self, *args, **kwargs):
        self.assert_message('warning', *args, **kwargs)

    def assert_error(self, *args, **kwargs):
        self.assert_message('error', *args, **kwargs)

    def assert_text(self, line_count, file_path):
        line_numbers = list(range(1, line_count + 1))
        file_content = self.app.fs_root.joinpath(file_path).read_text()

        if not file_content.endswith('\n'):
            file_content += '\n'

        linenos = self.body.findall('.//td[@class="linenos"]//span')
        code = self.body.find('.//td[@class="code"]//pre')

        actual_line_numbers = [int(span.text) for span in linenos]
        actual_file_content = list(code.itertext())[0]

        self.assertEqual(line_numbers, actual_line_numbers)
        self.assertEqual(file_content, actual_file_content)

    def assert_image(self, url):
        actual_url = self.body.find('.//img').get('src')

        self.assertEqual(url, actual_url)

    def assert_audio(self, url):
        actual_url = self.body.find('.//audio').get('src')

        self.assertEqual(url, actual_url)

    def assert_video(self, url):
        actual_url = self.body.find('.//video/source').get('src')

        self.assertEqual(url, actual_url)

    def assert_pdf(self, url):
        actual_url = self.body.find('.//embed').get('src')

        self.assertEqual(url, actual_url)

    def test_redirect_index(self):
        self.get('/')

        self.assert_redirect(303, 'http://localhost/fs/')

    def test_redirect_fs(self):
        self.get('/fs')

        self.assert_redirect(303, 'http://localhost/fs/')

    def test_fs_empty_directory(self):
        self.get('/fs/empty-dir/')

        self.assert_status_code(200)
        self.assert_title('webls: ./empty-dir/')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/', 'class': 'is-dir'},
            {'text': 'empty-dir', 'url': '/fs/empty-dir/', 'class': 'is-dir'},
        )
        self.assert_warning(
            message='directory is empty',
            path='./empty-dir/',
        )

    def test_fs_nonempty_directory(self):
        self.get('/fs/')

        self.assert_status_code(200)
        self.assert_title('webls: ./')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/', 'class': 'is-dir'},
        )
        self.assert_entries(
            {
                'mode': {'text': 'drwxrwxr-x'},
                'size': {'text': '4.0K', 'title': '4096 bytes'},
                'name': {
                    'class': 'is-dir',
                    'href': '/fs/empty-dir/',
                    'text': 'empty-dir/',
                    'title': 'empty-dir/',
                },
                'action': {},
            },
            {
                'mode': {'text': 'drwxrwxr-x'},
                'size': {'text': '4.0K', 'title': '4096 bytes'},
                'name': {
                    'class': 'is-dir',
                    'href': '/fs/nested/',
                    'text': 'nested/',
                    'title': 'nested/',
                },
                'action': {},
            },
            {
                'mode': {'text': '-rw-rw-r--'},
                'size': {'text': '73.4K', 'title': '75152 bytes'},
                'name': {
                    'class': 'is-file',
                    'href': '/fs/Lato-Regular.ttf',
                    'text': 'Lato-Regular.ttf',
                    'title': 'Lato-Regular.ttf',
                },
                'action': {
                    'href': '/dl/Lato-Regular.ttf',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
            {
                'mode': {'text': 'lrwxrwxrwx'},
                'size': {'text': '12B', 'title': '12 bytes'},
                'name': {
                    'class': 'is-symlink',
                    'href': '/fs/README.md',
                    'text': 'README.md -> ../README.md',
                    'title': 'README.md',
                },
                'action': {
                    'href': '/dl/README.md',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
            {
                'mode': {'text': '-rw-rw-r--'},
                'size': {'text': '1.6M', 'title': '1693405 bytes'},
                'name': {
                    'class': 'is-file',
                    'href': '/fs/audio.mp3',
                    'text': 'audio.mp3',
                    'title': 'audio.mp3',
                },
                'action': {
                    'href': '/dl/audio.mp3',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
            {
                'mode': {'text': 'lrwxrwxrwx'},
                'size': {'text': '14B', 'title': '14 bytes'},
                'name': {
                    'class': 'is-symlink-broken',
                    'href': '/fs/broken.txt',
                    'text': 'broken.txt -> inexistent.txt',
                    'title': 'broken.txt',
                },
                'action': {
                    'href': '/dl/broken.txt',
                    'text': '&#8623;',
                    'title': 'download'
                },
            },
            {
                'mode': {'text': 'crw-r--r--'},
                'size': {'text': '0B', 'title': '0 bytes'},
                'name': {
                    'class': 'is-char-device',
                    'href': '/fs/char_device',
                    'text': 'char_device',
                    'title': 'char_device',
                },
                'action': {
                    'href': '/dl/char_device',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
            {
                'mode': {'text': '-rw-r-----'},
                'size': {'text': '8.4M', 'title': '8817249 bytes'},
                'name': {
                    'class': 'is-file',
                    'href': '/fs/document.pdf',
                    'text': 'document.pdf',
                    'title': 'document.pdf',
                },
                'action': {
                    'href': '/dl/document.pdf',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
            {
                'mode': {'text': '-rw-rw-r--'},
                'size': {'text': '0B', 'title': '0 bytes'},
                'name': {
                    'class': 'is-file',
                    'href': '/fs/empty.txt',
                    'text': 'empty.txt',
                    'title': 'empty.txt',
                },
                'action': {
                    'href': '/dl/empty.txt',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
            {
                'mode': {'text': 'prw-rw-r--'},
                'size': {'text': '0B', 'title': '0 bytes'},
                'name': {
                    'class': 'is-fifo',
                    'href': '/fs/fifo',
                    'text': 'fifo',
                    'title': 'fifo',
                },
                'action': {
                    'href': '/dl/fifo',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
            {
                'mode': {'text': '-rw-rw-r--'},
                'size': {'text': '86.7K', 'title': '88731 bytes'},
                'name': {
                    'class': 'is-file',
                    'href': '/fs/image.jpg',
                    'text': 'image.jpg',
                    'title': 'image.jpg',
                },
                'action': {
                    'href': '/dl/image.jpg',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
            {
                'mode': {'text': '-rw-rw-r--'},
                'size': {'text': '1.2M', 'title': '1240001 bytes'},
                'name': {
                    'class': 'is-file',
                    'href': '/fs/large.txt',
                    'text': 'large.txt',
                    'title': 'large.txt',
                },
                'action': {
                    'href': '/dl/large.txt',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
            {
                'mode': {'text': '-rw-rw-r--'},
                'size': {'text': '3.5K', 'title': '3541 bytes'},
                'name': {
                    'class': 'is-file',
                    'href': '/fs/lorem.txt',
                    'text': 'lorem.txt',
                    'title': 'lorem.txt',
                },
                'action': {
                    'href': '/dl/lorem.txt',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
            {
                'mode': {'text': 'lrwxrwxrwx'},
                'size': {'text': '9B', 'title': '9 bytes'},
                'name': {
                    'class': 'is-symlink',
                    'href': '/fs/photo.jpg',
                    'text': 'photo.jpg -> image.jpg',
                    'title': 'photo.jpg',
                },
                'action': {
                    'href': '/dl/photo.jpg',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
            {
                'mode': {'text': 'srwxrwxr-x'},
                'size': {'text': '0B', 'title': '0 bytes'},
                'name': {
                    'class': 'is-socket',
                    'href': '/fs/unix.sock',
                    'text': 'unix.sock',
                    'title': 'unix.sock'
                },
                'action': {
                    'href': '/dl/unix.sock',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
            {
                'mode': {'text': '-rw-rw-r--'},
                'size': {'text': '16.7M', 'title': '17520898 bytes'},
                'name': {
                    'class': 'is-file',
                    'href': '/fs/video.mp4',
                    'text': 'video.mp4',
                    'title': 'video.mp4',
                },
                'action': {
                    'href': '/dl/video.mp4',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
        )

    def test_fs_nested_dir_entries(self):
        self.get('/fs/nested/')

        self.assert_status_code(200)
        self.assert_title('webls: ./nested/')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/', 'class': 'is-dir'},
            {'text': 'nested', 'url': '/fs/nested/', 'class': 'is-dir'},
        )
        self.assert_entries(
            {
                'mode': {'text': 'drwxrwxr-x'},
                'size': {'text': '4.0K', 'title': '4096 bytes'},
                'name': {
                    'class': 'is-dir',
                    'href': '/fs/nested/level-1/',
                    'text': 'level-1/',
                    'title': 'level-1/',
                },
                'action': {},
            },
            {
                'action': {
                    'href': '/dl/nested/file.txt',
                    'text': '&#8623;',
                    'title': 'download',
                },
                'mode': {'text': '-rw-rw-r--'},
                'name': {
                    'class': 'is-file',
                    'href': '/fs/nested/file.txt',
                    'text': 'file.txt',
                    'title': 'file.txt',
                },
                'size': {'text': '5B', 'title': '5 bytes'},
            }
        )

    def test_fs_inexisting_file(self):
        self.get('/fs/inexisting.txt')

        self.assert_status_code(404)
        self.assert_title('webls: ./inexisting.txt')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/', 'class': 'is-dir'},
            {
                'text': 'inexisting.txt',
                'url': '/fs/inexisting.txt',
                'class': 'is-file',
            },
        )
        self.assert_warning(
            message='not found',
            path='./inexisting.txt',
            url='/fs/',
            url_text='go to root',
        )

    def test_fs_empty_file(self):
        self.get('/fs/empty.txt')

        self.assert_status_code(200)
        self.assert_title('webls: ./empty.txt')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/', 'class': 'is-dir'},
            {'text': 'empty.txt', 'url': '/fs/empty.txt', 'class': 'is-file'},
        )
        self.assert_dl_btn('/dl/empty.txt')
        self.assert_warning(
            message='file is empty',
        )

    def test_fs_large_file(self):
        self.get('/fs/large.txt')

        self.assert_status_code(200)
        self.assert_title('webls: ./large.txt')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/', 'class': 'is-dir'},
            {'text': 'large.txt', 'url': '/fs/large.txt', 'class': 'is-file'},
        )
        self.assert_dl_btn('/dl/large.txt')
        self.assert_warning(
            message='file is too large (1.2M)',
        )

    def test_fs_binary_file(self):
        self.get('/fs/Lato-Regular.ttf')

        self.assert_status_code(200)
        self.assert_title('webls: ./Lato-Regular.ttf')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/', 'class': 'is-dir'},
            {
                'text': 'Lato-Regular.ttf',
                'url': '/fs/Lato-Regular.ttf',
                'class': 'is-file',
            },
        )
        self.assert_dl_btn('/dl/Lato-Regular.ttf')
        self.assert_warning(
            message='the contents cannot be displayed',
        )

    def test_fs_text_file(self):
        self.get('/fs/lorem.txt')

        self.assert_status_code(200)
        self.assert_title('webls: ./lorem.txt')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/', 'class': 'is-dir'},
            {'text': 'lorem.txt', 'url': '/fs/lorem.txt', 'class': 'is-file'},
        )
        self.assert_dl_btn('/dl/lorem.txt')
        self.assert_text(21, 'lorem.txt')

    def test_fs_image_file(self):
        self.get('/fs/image.jpg')

        self.assert_status_code(200)
        self.assert_title('webls: ./image.jpg')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/', 'class': 'is-dir'},
            {'text': 'image.jpg', 'url': '/fs/image.jpg', 'class': 'is-file'},
        )
        self.assert_dl_btn('/dl/image.jpg')
        self.assert_image('/dl/image.jpg')

    def test_fs_audio_file(self):
        self.get('/fs/audio.mp3')

        self.assert_status_code(200)
        self.assert_title('webls: ./audio.mp3')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/', 'class': 'is-dir'},
            {'text': 'audio.mp3', 'url': '/fs/audio.mp3', 'class': 'is-file'},
        )
        self.assert_dl_btn('/dl/audio.mp3')
        self.assert_audio('/dl/audio.mp3')

    def test_fs_video_file(self):
        self.get('/fs/video.mp4')

        self.assert_status_code(200)
        self.assert_title('webls: ./video.mp4')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/', 'class': 'is-dir'},
            {'text': 'video.mp4', 'url': '/fs/video.mp4', 'class': 'is-file'},
        )
        self.assert_dl_btn('/dl/video.mp4')
        self.assert_video('/dl/video.mp4')

    def test_fs_pdf_file(self):
        self.get('/fs/document.pdf')

        self.assert_status_code(200)
        self.assert_title('webls: ./document.pdf')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/', 'class': 'is-dir'},
            {
                'text': 'document.pdf',
                'url': '/fs/document.pdf',
                'class': 'is-file',
            },
        )
        self.assert_dl_btn('/dl/document.pdf')
        self.assert_pdf('/dl/document.pdf')

    def test_fs_symlink(self):
        self.get('/fs/photo.jpg')

        self.assert_status_code(200)
        self.assert_title('webls: ./photo.jpg')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/', 'class': 'is-dir'},
            {'text': 'photo.jpg', 'url': '/fs/photo.jpg', 'class': 'is-file'},
        )
        self.assert_dl_btn('/dl/photo.jpg')
        self.assert_image('/dl/photo.jpg')

    def test_fs_broken_symlink(self):
        self.get('/fs/broken.txt')

        self.assert_status_code(404)
        self.assert_title('webls: ./broken.txt')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/', 'class': 'is-dir'},
            {'text': 'broken.txt', 'url': '/fs/broken.txt', 'class': 'is-file'},
        )
        self.assert_warning(
            message='not found',
            path='./broken.txt',
            url='/fs/',
            url_text='go to root',
        )

    def test_fs_symlink_outside_root(self):
        self.get('/fs/README.md')

        self.assert_status_code(403)
        self.assert_error(
            message='forbidden',
            path='./README.md',
            url='/fs/',
            url_text='go to root',
        )

    def test_fs_socket(self):
        self.get('/fs/unix.sock')

        self.assert_status_code(403)
        self.assert_error(
            message='forbidden',
            path='./unix.sock',
            url='/fs/',
            url_text='go to root',
        )

    def test_fs_fifo(self):
        self.get('/fs/fifo')

        self.assert_status_code(403)
        self.assert_error(
            message='forbidden',
            path='./fifo',
            url='/fs/',
            url_text='go to root',
        )

    def test_fs_device(self):
        self.get('/fs/char_device')

        self.assert_status_code(403)
        self.assert_error(
            message='forbidden',
            path='./char_device',
            url='/fs/',
            url_text='go to root',
        )

    def test_fs_dir_no_trailing_slash(self):
        self.get('/fs/empty-dir')

        self.assert_status_code(404)
        self.assert_title('webls: ./empty-dir')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/', 'class': 'is-dir'},
            {'text': 'empty-dir', 'url': '/fs/empty-dir/', 'class': 'is-dir'},
        )
        self.assert_warning(
            message='not found',
            path='./empty-dir',
            url='/fs/',
            url_text='go to root',
        )

    def test_fs_file_trailing_slash(self):
        self.get('/fs/image.jpg/')

        self.assert_status_code(404)
        self.assert_title('webls: ./image.jpg/')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/', 'class': 'is-dir'},
            {'text': 'image.jpg', 'url': '/fs/image.jpg', 'class': 'is-file'},
        )
        self.assert_warning(
            message='not found',
            path='./image.jpg/',
            url='/fs/',
            url_text='go to root',
        )

    def test_fs_path_traversal_attack(self):
        self.get('/fs/../../')

        self.assert_status_code(403)
        self.assert_error(
            message='forbidden',
            path='./../../',
            url='/fs/',
            url_text='go to root',
        )

    def test_fs_path_traversal_attack_encoded(self):
        self.get('/fs/%2e%2e%2f%2e%2e%2f')

        self.assert_status_code(403)
        self.assert_error(
            message='forbidden',
            path='./../../',
            url='/fs/',
            url_text='go to root',
        )

    def test_fs_path_traversal_attack_double_encoded(self):
        self.get('/fs/%252e%252e%252f%252e%252e%252f')

        self.assert_status_code(404)
        self.assert_warning(
            message='not found',
            path='./%2e%2e%2f%2e%2e%2f',
            url='/fs/',
            url_text='go to root',
        )

    def test_dl_inexistent_file(self):
        self.get('/dl/inexisting.txt')

        self.assert_status_code(404)
        self.assertEqual(
            'not found: GET /dl/inexisting.txt',
            self.response.text,
        )

    def test_dl_directory(self):
        self.get('/dl/empty-dir')

        self.assert_status_code(404)
        self.assertEqual(
            'not found: GET /dl/empty-dir',
            self.response.text,
        )

    def test_dl_broken_symlink(self):
        self.get('/dl/broken.txt')

        self.assert_status_code(404)
        self.assertEqual(
            'not found: GET /dl/broken.txt',
            self.response.text,
        )

    def test_dl_symlink_outside_root(self):
        self.get('/dl/README.md')

        self.assert_status_code(403)
        self.assertEqual(
            'forbidden: GET /dl/README.md',
            self.response.text,
        )

    def test_dl_socket(self):
        self.get('/dl/unix.sock')

        self.assert_status_code(403)
        self.assertEqual(
            'forbidden: GET /dl/unix.sock',
            self.response.text,
        )

    def test_dl_fifo(self):
        self.get('/dl/fifo')

        self.assert_status_code(403)
        self.assertEqual(
            'forbidden: GET /dl/fifo',
            self.response.text,
        )

    def test_dl_device(self):
        self.get('/dl/char_device')

        self.assert_status_code(403)
        self.assertEqual(
            'forbidden: GET /dl/char_device',
            self.response.text,
        )

    def test_dl_dir_no_trailing_slash(self):
        self.get('/dl/empty-dir')

        self.assert_status_code(404)
        self.assertEqual(
            'not found: GET /dl/empty-dir',
            self.response.text,
        )

    def test_dl_file_trailing_slash(self):
        self.get('/dl/image.jpg/')

        self.assert_status_code(404)
        self.assertEqual(
            'not found: GET /dl/image.jpg/',
            self.response.text,
        )

    def test_dl_path_traversal_attack(self):
        self.get('/dl/../../')

        self.assert_status_code(403)
        self.assertEqual(
            'forbidden: GET /dl/../../',
            self.response.text,
        )

    def test_fs_path_traversal_attack_encoded(self):
        self.get('/dl/%2e%2e%2f%2e%2e%2f')

        self.assert_status_code(403)
        self.assertEqual(
            'forbidden: GET /dl/../../',
            self.response.text,
        )

    def test_fs_path_traversal_attack_double_encoded(self):
        self.get('/dl/%252e%252e%252f%252e%252e%252f')

        self.assert_status_code(404)
        self.assertEqual(
            'not found: GET /dl/%2e%2e%2f%2e%2e%2f',
            self.response.text,
        )


if __name__ == '__main__':
    unittest.main()
