from .structs import *


class CompUrl:
    def __init__(self, header, ns, url):
        self.header = header
        self.ns = ns
        self.url = url

    def __call__(self, index):
        urlPtrList = UrlPtrList(self.header.buf, self.header.urlPtrPos)
        d = Dirent(self.header.buf, urlPtrList[index])
        if d.namespace == self.ns and d.url == self.url:
            return 0

        if d.namespace < self.ns or (d.namespace == self.ns and d.url < self.url):
            return -1
        else:
            return 1


class CompTitle:
    def __init__(self, header, ns, title):
        self.header = header
        self.ns = ns
        self.title = title

    def __call__(self, index):
        titlePtrList = TitlePtrList(self.header.buf, self.header.titlePtrPos)
        urlIndex = titlePtrList[index]
        urlPtrList = UrlPtrList(self.header.buf, self.header.urlPtrPos)
        d = Dirent(self.header.buf, urlPtrList[urlIndex])
        title = d.title or d.url
        if d.namespace == self.ns and title == self.title:
            return 0

        if d.namespace < self.ns or (d.namespace == self.ns and title < self.title):
            return -1
        else:
            return 1


def bisect(comparator, low, high):
    while low < high:
        middle = (low + high) // 2
        comp = comparator(middle)
        if comp == 0:
            return middle
        if comp < 0:
            low = middle
        else:
            high = middle

    raise IndexError


def findByUrl(header, ns, url):
    urlComp = CompUrl(header, ns, url)
    return bisect(urlComp, 0, header.articleCount)


def findByTitle(header, ns, title):
    titleComp = CompTitle(header, ns, title)
    return bisect(titleComp, 0, header.articleCount)
