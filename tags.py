#!/usr/bin/python
import os
import stat
import fuse
import errno
import sys

fuse.fuse_python_api = (0, 2)


class tagFS(fuse.Fuse):
    __file_id = {}
    __filename_id = {}
    __id_file = {}
    __tag_id = {}
    __id_tag = {}
    __tag_files = {}
    __file_tags = {}
    __logfile = 0
    __basepath = ""

    def __init__(self, *args, **kw):
        if len(sys.argv) > 2:
            self.__basepath = os.path.abspath(sys.argv[1])
        else:
            self.__basepath = "/media/enc"
        self.__logfile = open("/tmp/tags.log", "a")
        self.__read()
        fuse.Fuse.__init__(self, *args, **kw)

    def getattr(self, path):
        st = fuse.Stat()
        st.st_mode = 0
        st.st_ino = 0
        st.st_dev = 0
        st.st_nlink = 0
        st.st_uid = 0
        st.st_gid = 0
        st.st_size = 0
        st.st_atime = 0
        st.st_mtime = 0
        st.st_ctime = 0
        if path == '/':
            st.st_mode = stat.S_IFDIR | 0755
            st.st_nlink = len(self.__id_tag)
        else:
            (p, n) = os.path.split(path)
            if n in self.__filename_id:
                for tag in p.split('/')[1:]:
                    if not self.__tag_id[tag] in self.__file_tags[self.__filename_id[n]]:
                        return -errno.ENOENT
                st.st_mode = stat.S_IFLNK | 0644
                tmp = os.stat(self.__id_file[self.__filename_id[n]])
                st.st_uid = tmp.st_uid
                st.st_gid = tmp.st_gid
                st.st_size = tmp.st_size
                st.st_atime = tmp.st_atime
                st.st_mtime = tmp.st_mtime
                st.st_ctime = tmp.st_ctime
                st.st_nlink = tmp.st_nlink
            elif n in self.__tag_id:
                tmp = os.stat(os.path.join(self.__basepath, "tags", n))
                st.st_mode = stat.S_IFDIR | 0755
                st.st_uid = tmp.st_uid
                st.st_gid = tmp.st_gid
                st.st_size = tmp.st_size
                st.st_atime = tmp.st_atime
                st.st_mtime = tmp.st_mtime
                st.st_ctime = tmp.st_ctime

                tags = set()
                for i in path.split('/'):
                    if len(i):
                        tags.add(self.__tag_id[i])

                st.st_nlink = len(self.__findfiles(tags)) + len(self.__findchildtags(tags))
                st.st_size = 0
            else:
                return -errno.ENOENT
        return st

    def unlink(self, path):
        (p, n) = os.path.split(path)
        fileid = self.__filename_id[n]
        for tag in p.split('/'):
            if len(tag):
                tagid = self.__tag_id[tag]
                os.unlink(os.path.join(self.__basepath, "tags", tag, n))
                self.__tag_files[tagid].remove(fileid)
                self.__file_tags[fileid].remove(tagid)

        return 0

    def __log(self, s):
        self.__logfile.write(s)
        self.__logfile.flush()

    def __dump(self):
        print >>self.__logfile, "ID to FILE"
        print >>self.__logfile, self.__id_file
        print >>self.__logfile
        print >>self.__logfile, "FILE to ID"
        print >>self.__logfile, self.__file_id
        print >>self.__logfile
        print >>self.__logfile, "ID to TAG"
        print >>self.__logfile, self.__id_tag
        print >>self.__logfile
        print >>self.__logfile, "TAG to ID"
        print >>self.__logfile, self.__tag_id
        print >>self.__logfile
        print >>self.__logfile, "FILENAME to ID"
        print >>self.__logfile, self.__filename_id
        print >>self.__logfile
        print >>self.__logfile, "FILE to TAG"
        print >>self.__logfile, self.__file_tags
        print >>self.__logfile
        print >>self.__logfile, "TAG to FILE"
        print >>self.__logfile, self.__tag_files
        print >>self.__logfile
        print >>self.__logfile

    def __addfile(self, filename, path):
        try:
            fileid = max(self.__id_file)+1
        except:
            fileid = 1
        self.__file_id[path] = fileid
        self.__id_file[fileid] = path
        self.__filename_id[filename] = fileid
        self.__file_tags[fileid] = set()
        return fileid

    def symlink(self, targetPath, linkPath):
        if not os.path.isabs(targetPath) or not os.path.isfile(targetPath):
            # TODO: syslog("Refusing to create a symlink: either oldpath is not absolute or there is no such file in filesystem")
            return -errno.EFAULT

        target = os.path.relpath(targetPath, os.path.join(self.__basepath, "tags/tag"))
        filename = os.path.basename(targetPath)

        fileid = self.__file_id.get(targetPath)
        if fileid is None:
            fileid = self.__addfile(filename, targetPath)

        for tag in linkPath.split("/")[1:-1]:
            tagid = self.__tag_id[tag]
            self.__file_tags[fileid].add(tagid)
            self.__tag_files[tagid].add(fileid)
            try:
                os.symlink(target, os.path.join(self.__basepath, "tags", tag, filename))
            except:
                pass
#                print "I/O error({0}): {1}".format(e.errno, e.strerror)

        return 0

    def __addtag(self, tag):
        try:
            tagid = max(self.__id_tag)+1
        except:
            tagid = 1
        self.__id_tag[tagid] = tag
        self.__tag_id[tag] = tagid
        self.__tag_files[tagid] = set()
        return tagid

    def mkdir(self, path, mode):
        (p, n) = os.path.split(path)
        self.__addtag(n)
        ret = os.mkdir(os.path.join(self.__basepath, 'tags', n), mode)
        return ret

    def readlink(self, path):
        (p, n) = os.path.split(path)
        if n in self.__filename_id:
            return self.__id_file[self.__filename_id[n]]
        return ""

    def statfs(self):
        st = fuse.StatVfs()
        st.f_bsize = 1024
        st.f_frsize = 1024
        st.f_bfree = 0
        st.f_bavail = 0
        st.f_files = 10
        st.f_blocks = 0
        st.f_ffree = 0
        st.f_favail = 0
        st.f_namelen = 255
        return st

    def __read(self):
        for dirname in os.listdir(os.path.join(self.__basepath, "tags")):
            (tmp, tag) = os.path.split(dirname)
            if not tag in self.__tag_id:
                self.__addtag(tag)

        for dirname, dirnames, filenames in os.walk(os.path.join(self.__basepath, "tags")):
            for filename in filenames:
                path = os.path.join(dirname, filename)
                (tmp, tag) = os.path.split(dirname)

                fullpathname = os.path.abspath(os.path.join(dirname, os.readlink(path)))
                if not fullpathname in self.__file_id:
                    fileid = self.__addfile(filename, fullpathname)
                else:
                    fileid = self.__file_id[fullpathname]

                tagid = self.__tag_id[tag]
                self.__tag_files[tagid].add(fileid)

                if not fileid in self.__file_tags:
                    self.__file_tags[fileid] = set()
                self.__file_tags[fileid].add(tagid)

    def rmdir(self, path):
        return -errno.ENOENT
        (tmp, tag) = os.path.split(path)

        tagid = self.__tag_id[tag]
        for fileid in self.__tag_files[tagid]:
            print fileid
            self.__file_tags[fileid].remove(tagid)
        del self.__tag_id[tag]
        del self.__id_tag[tagid]
        del self.__tag_files[tagid]
        return 0

    def __findfiles(self, tags):
        tmp = set(self.__id_file)
        for i in tags:
            tmp = tmp.intersection(self.__tag_files[i])
        return tmp

    def __findchildtags(self, tags):
        childtags = set()
        for i in self.__findfiles(tags):
            childtags = childtags.union(self.__file_tags[i])
        return childtags.difference(tags)

    def readdir(self, path, offset):
        yield fuse.Direntry('.')
        yield fuse.Direntry('..')
        if path == '/':
            for i in self.__id_tag:
                yield fuse.Direntry(self.__id_tag[i])
        else:
            tags = set()
            for i in path.split('/'):
                if len(i):
                    tags.add(self.__tag_id[i])

            childtags = self.__findchildtags(tags)
            for i in childtags:
                yield fuse.Direntry(self.__id_tag[i])

            files = self.__findfiles(tags)
            for i in files:
                (p, name) = os.path.split(self.__id_file[i])
                yield fuse.Direntry(name)


def runTagFS():
    usage = 'Tag FS ' + fuse.Fuse.fusage
    fs = tagFS(version="%prog " + fuse.__version__, usage=usage, dash_s_do='setsingle')
    fs.parse(errex=1)
    fs.main()

runTagFS()

