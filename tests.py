import html5lib
import os
import unittest
import webls

from pathlib import Path
from werkzeug.test import Client


class TestWebls(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.app = webls.app_build(development=False)
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
        actual_location = self.response.headers['Location']

        self.assert_status_code(code)
        self.assertEqual(location, actual_location)

    def assert_title(self, title):
        actual_title = self.body.find('.//title').text

        self.assertEqual(title, actual_title)

    def assert_crumbs(self, *crumbs):
        actual_crumbs = [
            {
                'text': a.find('code').text,
                'url': a.get('href'),
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

    def assert_text(self, line_count, file_content):
        line_numbers = '\n'.join([
            f'{number}.'
            for number in range(1, line_count + 1)
        ])

        actual_line_numbers = self.body.find('.//div[@class="line-numbers"]').text
        actual_file_content = self.body.find('.//div[@class="file-content"]').text

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
        self.get('/fs/demo/empty-dir/')

        self.assert_status_code(200)
        self.assert_title('webls: demo/empty-dir')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/'},
            {'text': 'demo', 'url': '/fs/demo'},
            {'text': 'empty-dir', 'url': '/fs/demo/empty-dir'},
        )
        self.assert_warning(
            message='directory is empty',
            path='demo/empty-dir',
        )

    def test_fs_nonempty_directory(self):
        self.get('/fs/demo/')

        self.assert_status_code(200)
        self.assert_title('webls: demo')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/'},
            {'text': 'demo', 'url': '/fs/demo'},
        )
        self.assert_entries(
            {
                'mode': {'text': 'drwxrwxr-x'},
                'size': {'text': '4.0K', 'title': '4096 bytes'},
                'name': {
                    'class': 'is-dir',
                    'href': '/fs/demo/empty-dir/',
                    'text': 'empty-dir/',
                    'title': 'empty-dir/',
                },
                'action': {},
            },
            {
                'mode': {'text': '-rw-rw-r--'},
                'size': {'text': '73.4K', 'title': '75152 bytes'},
                'name': {
                    'class': 'is-file',
                    'href': '/fs/demo/Lato-Regular.ttf',
                    'text': 'Lato-Regular.ttf',
                    'title': 'Lato-Regular.ttf',
                },
                'action': {
                    'href': '/dl/demo/Lato-Regular.ttf',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
            {
                'mode': {'text': 'lrwxrwxrwx'},
                'size': {'text': '12B', 'title': '12 bytes'},
                'name': {
                    'class': 'is-symlink',
                    'href': '/fs/demo/README.md',
                    'text': 'README.md -> ../README.md',
                    'title': 'README.md',
                },
                'action': {
                    'href': '/dl/demo/README.md',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
            {
                'mode': {'text': '-rw-rw-r--'},
                'size': {'text': '1.6M', 'title': '1693405 bytes'},
                'name': {
                    'class': 'is-file',
                    'href': '/fs/demo/audio.mp3',
                    'text': 'audio.mp3',
                    'title': 'audio.mp3',
                },
                'action': {
                    'href': '/dl/demo/audio.mp3',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
            {
                'mode': {'text': 'lrwxrwxrwx'},
                'size': {'text': '14B', 'title': '14 bytes'},
                'name': {
                    'class': 'is-symlink-broken',
                    'href': '/fs/demo/broken.txt',
                    'text': 'broken.txt -> inexistent.txt',
                    'title': 'broken.txt',
                },
                'action': {
                    'href': '/dl/demo/broken.txt',
                    'text': '&#8623;',
                    'title': 'download'
                },
            },
            {
                'mode': {'text': 'crw-r--r--'},
                'size': {'text': '0B', 'title': '0 bytes'},
                'name': {
                    'class': 'is-char-device',
                    'href': '/fs/demo/char_device',
                    'text': 'char_device',
                    'title': 'char_device',
                },
                'action': {
                    'href': '/dl/demo/char_device',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
            {
                'mode': {'text': '-rw-r-----'},
                'size': {'text': '8.4M', 'title': '8817249 bytes'},
                'name': {
                    'class': 'is-file',
                    'href': '/fs/demo/document.pdf',
                    'text': 'document.pdf',
                    'title': 'document.pdf',
                },
                'action': {
                    'href': '/dl/demo/document.pdf',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
            {
                'mode': {'text': '-rw-rw-r--'},
                'size': {'text': '0B', 'title': '0 bytes'},
                'name': {
                    'class': 'is-file',
                    'href': '/fs/demo/empty.txt',
                    'text': 'empty.txt',
                    'title': 'empty.txt',
                },
                'action': {
                    'href': '/dl/demo/empty.txt',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
            {
                'mode': {'text': 'prw-rw-r--'},
                'size': {'text': '0B', 'title': '0 bytes'},
                'name': {
                    'class': 'is-fifo',
                    'href': '/fs/demo/fifo',
                    'text': 'fifo',
                    'title': 'fifo',
                },
                'action': {
                    'href': '/dl/demo/fifo',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
            {
                'mode': {'text': '-rw-rw-r--'},
                'size': {'text': '86.7K', 'title': '88731 bytes'},
                'name': {
                    'class': 'is-file',
                    'href': '/fs/demo/image.jpg',
                    'text': 'image.jpg',
                    'title': 'image.jpg',
                },
                'action': {
                    'href': '/dl/demo/image.jpg',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
            {
                'mode': {'text': '-rw-rw-r--'},
                'size': {'text': '1.2M', 'title': '1240001 bytes'},
                'name': {
                    'class': 'is-file',
                    'href': '/fs/demo/large.txt',
                    'text': 'large.txt',
                    'title': 'large.txt',
                },
                'action': {
                    'href': '/dl/demo/large.txt',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
            {
                'mode': {'text': '-rw-rw-r--'},
                'size': {'text': '3.5K', 'title': '3541 bytes'},
                'name': {
                    'class': 'is-file',
                    'href': '/fs/demo/lorem.txt',
                    'text': 'lorem.txt',
                    'title': 'lorem.txt',
                },
                'action': {
                    'href': '/dl/demo/lorem.txt',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
            {
                'mode': {'text': 'lrwxrwxrwx'},
                'size': {'text': '9B', 'title': '9 bytes'},
                'name': {
                    'class': 'is-symlink',
                    'href': '/fs/demo/photo.jpg',
                    'text': 'photo.jpg -> image.jpg',
                    'title': 'photo.jpg',
                },
                'action': {
                    'href': '/dl/demo/photo.jpg',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
            {
                'mode': {'text': 'srwxrwxr-x'},
                'size': {'text': '0B', 'title': '0 bytes'},
                'name': {
                    'class': 'is-socket',
                    'href': '/fs/demo/unix.sock',
                    'text': 'unix.sock',
                    'title': 'unix.sock'
                },
                'action': {
                    'href': '/dl/demo/unix.sock',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
            {
                'mode': {'text': '-rw-rw-r--'},
                'size': {'text': '16.7M', 'title': '17520898 bytes'},
                'name': {
                    'class': 'is-file',
                    'href': '/fs/demo/video.mp4',
                    'text': 'video.mp4',
                    'title': 'video.mp4',
                },
                'action': {
                    'href': '/dl/demo/video.mp4',
                    'text': '&#8623;',
                    'title': 'download',
                },
            },
        )

    def test_fs_inexisting_file(self):
        self.get('/fs/demo/inexisting.txt')

        self.assert_status_code(404)
        self.assert_title('webls: demo/inexisting.txt')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/'},
            {'text': 'demo', 'url': '/fs/demo'},
            {'text': 'inexisting.txt', 'url': '/fs/demo/inexisting.txt'},
        )
        self.assert_warning(
            message='file not found',
            path='demo/inexisting.txt',
            url='/fs/',
            url_text='go to root',
        )

    def test_fs_empty_file(self):
        self.get('/fs/demo/empty.txt')

        self.assert_status_code(200)
        self.assert_title('webls: demo/empty.txt')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/'},
            {'text': 'demo', 'url': '/fs/demo'},
            {'text': 'empty.txt', 'url': '/fs/demo/empty.txt'},
        )
        self.assert_dl_btn('/dl/demo/empty.txt')
        self.assert_warning(
            message='file is empty',
        )

    def test_fs_large_file(self):
        self.get('/fs/demo/large.txt')

        self.assert_status_code(200)
        self.assert_title('webls: demo/large.txt')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/'},
            {'text': 'demo', 'url': '/fs/demo'},
            {'text': 'large.txt', 'url': '/fs/demo/large.txt'},
        )
        self.assert_dl_btn('/dl/demo/large.txt')
        self.assert_warning(
            message='file is too large (1.2M)',
        )

    def test_fs_binary_file(self):
        self.get('/fs/demo/Lato-Regular.ttf')

        self.assert_status_code(200)
        self.assert_title('webls: demo/Lato-Regular.ttf')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/'},
            {'text': 'demo', 'url': '/fs/demo'},
            {'text': 'Lato-Regular.ttf', 'url': '/fs/demo/Lato-Regular.ttf'},
        )
        self.assert_dl_btn('/dl/demo/Lato-Regular.ttf')
        self.assert_warning(
            message='the contents cannot be displayed',
        )

    def test_fs_text_file(self):
        self.get('/fs/demo/lorem.txt')

        self.assert_status_code(200)
        self.assert_title('webls: demo/lorem.txt')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/'},
            {'text': 'demo', 'url': '/fs/demo'},
            {'text': 'lorem.txt', 'url': '/fs/demo/lorem.txt'},
        )
        self.assert_dl_btn('/dl/demo/lorem.txt')
        self.assert_text(21, Path('demo/lorem.txt').read_text())

    def test_fs_image_file(self):
        self.get('/fs/demo/image.jpg')

        self.assert_status_code(200)
        self.assert_title('webls: demo/image.jpg')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/'},
            {'text': 'demo', 'url': '/fs/demo'},
            {'text': 'image.jpg', 'url': '/fs/demo/image.jpg'},
        )
        self.assert_dl_btn('/dl/demo/image.jpg')
        self.assert_image('/dl/demo/image.jpg')

    def test_fs_audio_file(self):
        self.get('/fs/demo/audio.mp3')

        self.assert_status_code(200)
        self.assert_title('webls: demo/audio.mp3')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/'},
            {'text': 'demo', 'url': '/fs/demo'},
            {'text': 'audio.mp3', 'url': '/fs/demo/audio.mp3'},
        )
        self.assert_dl_btn('/dl/demo/audio.mp3')
        self.assert_audio('/dl/demo/audio.mp3')

    def test_fs_video_file(self):
        self.get('/fs/demo/video.mp4')

        self.assert_status_code(200)
        self.assert_title('webls: demo/video.mp4')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/'},
            {'text': 'demo', 'url': '/fs/demo'},
            {'text': 'video.mp4', 'url': '/fs/demo/video.mp4'},
        )
        self.assert_dl_btn('/dl/demo/video.mp4')
        self.assert_video('/dl/demo/video.mp4')

    def test_fs_pdf_file(self):
        self.get('/fs/demo/document.pdf')

        self.assert_status_code(200)
        self.assert_title('webls: demo/document.pdf')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/'},
            {'text': 'demo', 'url': '/fs/demo'},
            {'text': 'document.pdf', 'url': '/fs/demo/document.pdf'},
        )
        self.assert_dl_btn('/dl/demo/document.pdf')
        self.assert_pdf('/dl/demo/document.pdf')

    def test_fs_symlink(self):
        self.get('/fs/demo/photo.jpg')

        self.assert_status_code(200)
        self.assert_title('webls: demo/photo.jpg')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/'},
            {'text': 'demo', 'url': '/fs/demo'},
            {'text': 'photo.jpg', 'url': '/fs/demo/photo.jpg'},
        )
        self.assert_dl_btn('/dl/demo/photo.jpg')
        self.assert_image('/dl/demo/photo.jpg')

    def test_fs_broken_symlink(self):
        self.get('/fs/demo/broken.txt')

        self.assert_status_code(404)
        self.assert_title('webls: demo/broken.txt')
        self.assert_crumbs(
            {'text': '.', 'url': '/fs/'},
            {'text': 'demo', 'url': '/fs/demo'},
            {'text': 'broken.txt', 'url': '/fs/demo/broken.txt'},
        )
        self.assert_warning(
            message='file not found',
            path='demo/broken.txt',
            url='/fs/',
            url_text='go to root',
        )

    @unittest.skip('get rid of `os.chdir` and set fs_root')
    def test_fs_symlink_outside_root(self):
        self.get('/fs/demo/README.md')

        self.assert_status_code(403)
        self.assert_error(
            message='forbidden',
            path='demo/README.md',
        )

    def test_fs_socket(self):
        self.get('/fs/demo/unix.sock')

        self.assert_status_code(403)
        self.assert_error(
            message='forbidden',
            path='demo/unix.sock',
            url='/fs/',
            url_text='go to root',
        )

    def test_fs_fifo(self):
        self.get('/fs/demo/fifo')

        self.assert_status_code(403)
        self.assert_error(
            message='forbidden',
            path='demo/fifo',
            url='/fs/',
            url_text='go to root',
        )

    def test_fs_device(self):
        self.get('/fs/demo/char_device')

        self.assert_status_code(403)
        self.assert_error(
            message='forbidden',
            path='demo/char_device',
            url='/fs/',
            url_text='go to root',
        )

    def test_dl_inexistent_file(self):
        self.get('/dl/demo/inexisting.txt')

        self.assert_status_code(404)
        self.assertEqual(
            'not found: GET /dl/demo/inexisting.txt',
            self.response.text,
        )

    def test_dl_directory(self):
        self.get('/dl/demo/empty-dir')

        self.assert_status_code(404)
        self.assertEqual(
            'not found: GET /dl/demo/empty-dir',
            self.response.text,
        )

    def test_dl_broken_symlink(self):
        self.get('/dl/demo/broken.txt')

        self.assert_status_code(404)
        self.assertEqual(
            'not found: GET /dl/demo/broken.txt',
            self.response.text,
        )

    @unittest.skip('get rid of `os.chdir` and set fs_root')
    def test_dl_symlink_outside_root(self):
        self.get('/dl/demo/README.md')

        self.assert_status_code(403)
        self.assertEqual(
            'forbidden: GET /dl/demo/README.md',
            self.response.text,
        )

    def test_dl_socket(self):
        self.get('/dl/demo/unix.sock')

        self.assert_status_code(403)
        self.assertEqual(
            'forbidden: GET /dl/demo/unix.sock',
            self.response.text,
        )

    def test_dl_fifo(self):
        self.get('/dl/demo/fifo')

        self.assert_status_code(403)
        self.assertEqual(
            'forbidden: GET /dl/demo/fifo',
            self.response.text,
        )

    def test_dl_device(self):
        self.get('/dl/demo/char_device')

        self.assert_status_code(403)
        self.assertEqual(
            'forbidden: GET /dl/demo/char_device',
            self.response.text,
        )


if __name__ == '__main__':
    unittest.main()
