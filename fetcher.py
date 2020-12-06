#!/usr/bin/env python3

import os
import re
import sys
import errno
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup


FETCHER_DIR = ""
NETLOC_DIR = ""
ARTICLE_DIR = ""
ARTICLE_IMAGES_DIR = ""


def mkdirs(path):
    """
    Creating the given path if does not exist using the EAFP method.
    EAFP = Easier to ask for forgiveness than permission.
    """
    try:
        os.makedirs(path)
    except OSError as err:
        if err.errno != errno.EEXIST:
            raise


def text2dirname(text):
    """
    Replaces whitespaces of a text with underscores. No whitespace in paths
    is the goal.
    """
    result = re.sub(r"\s+", '_', text)
    return result


def setup_local_workspace(netloc, article_title):
    "Setup the local environment. For example local storage."
    global FETCHER_DIR, NETLOC_DIR, ARTICLE_DIR, ARTICLE_IMAGES_DIR
    home_dir = os.getenv('HOME')
    article_title_as_dirname = text2dirname(article_title)

    FETCHER_DIR = os.path.join(home_dir, ".fetcher")
    NETLOC_DIR = os.path.join(FETCHER_DIR, netloc)
    ARTICLE_DIR = os.path.join(NETLOC_DIR, article_title_as_dirname)
    ARTICLE_IMAGES_DIR = os.path.join(ARTICLE_DIR, "images")

    mkdirs(ARTICLE_IMAGES_DIR)


def validate_url(url):
    "Check if URL is valid."
    parsed_url = urlparse(url)
    if parsed_url.scheme and parsed_url.netloc:
        return True

    return False


def get_url_scheme(url):
    "Get the scheme of a URL."
    parsed_url = urlparse(url)
    return parsed_url.scheme


def get_url_netloc(url):
    "Extract the NETwork LOCality (netloc) out of a URL."
    parsed_url = urlparse(url)
    return parsed_url.netloc


def evaluate_cmd():
    """
    Evaluate the command line arguments or exit with help printed if none
    given.
    """
    url_arg = sys.argv[1]

    if len(sys.argv) <= 1:
        print(__doc__)
        sys.exit(0)

    if len(sys.argv) > 2:
        print("The script takes only 1 argument - a URL!")

    if not validate_url(url_arg):
        print(
            "\n\n\nERROR: The URL '{}' {}!\n\n\n".format(
                url_arg,
                "you have given is invalid"
            )
        )
        sys.exit(1)

    return url_arg


def is_tag_visible(tag):
    "Checks if a given element is visible in the article"
    style = tag.attrs.get('style', False)
    if style and ('hidden' in style or 'display: none' in style or 'display:none' in style):
        return False

    parent = tag.parent
    if parent and not is_tag_visible(parent):
        return False

    return True


def remove_footer(content):
    "Removes footer of an article, if such exists."
    footer = content.find('footer')

    if not footer:
        footer = content.find('div', class_='footer')

    footer.decompose()

    return content


def download_img(url, filename):
    "Downloads image"
    request = requests.get(url)
    if request.ok:
        with open(filename, 'wb') as img_file:
            img_file.write(request.content)


if __name__ == "__main__":
    target_url = evaluate_cmd()
    response = requests.get(target_url)

    if not response.ok:
        print(
            "\n\n\nERROR: Status code: {}!\n\n\n".format(
                response.status_code
            )
        )
        sys.exit(2)

    content = response.text
    content_parsed = BeautifulSoup(content, "html.parser")
    content_parsed = remove_footer(content_parsed)
    title = content_parsed.title.string
    print(title)

    articles = content_parsed.find_all('article')
    paragraphs = content_parsed.find_all('p')
    if articles:
        for article in articles:
            if(is_tag_visible(article)):
                print(article.prettify())
    else:
        for p in paragraphs:
            if(is_tag_visible(p)):
                print(p.prettify())

    for img in content_parsed.find_all('img'):
        img_src = img.get('src')
        if not validate_url(img_src):
            img_src = ''.join([
                get_url_scheme(target_url),
                "://",
                get_url_netloc(target_url),
                img_src
            ])
        if not validate_url(img_src):
            next
        download_img(img_src, "./test.jpg")
        break
