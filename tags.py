#!/usr/bin/python
import os, sys, stat, fuse;

basepath = '/media/enc/'
fuse.fuse_python_api = (0, 2)

class tagFS(fuse.Fuse) :
    __file_id = {}
    __filename_id = {}
    __id_file = {}
    __tag_id = {}
    __id_tag = {}
    __tag_files = {}
    __file_tags = {}

    def __init__(self, *args, **kw):
        fuse.Fuse.__init__(self, *args, **kw)
        self.__read()

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
                tmp = os.stat(os.path.join(basepath, "tags", n))
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

                st.st_nlink = len(self.__findfiles(tags))+len(self.__findchildtags(tags))
                st.st_size = 0
            else:
                return -errno.ENOENT
        return st

    def unlink(self, path):
        (p,n) = os.path.split(path)
        id = self.__file_id[n]
        del self.__file_id[n]
        del self.__id_file[n]
        del self.__file_tags[id]
        for i in self.__tag_files:
            self.__tag_files[i].remove(id)

    def mkdir(self, path, mode):
        (p,n) = os.path.split(path)
        id = len(self.__id_tag)+1
        self.__id_tag[id] = n
        self.__tag_id[n] = id
        self.__file_tags[1].add(id)
        self.__tag_files[id].set([id])
        os.mkdir(os.path.join(basepath,'tags',n), mode)

    def mknod(self, path, mode, dev):
        f = open("/tmp/out.txt", "a")
        f.write("Nod: "+path+" "+str(mode))
        f.close()
        (p,n) = os.path.split(path)
        id = len(self.__id_tag)+1
        self.__id_tag[id] = n
        self.__tag_id[n] = id
        self.__file_tags[1].add(id)
        self.__tag_files[id].set([id])
        os.mkdir(os.path.join(basepath,'tags',n), mode)

    def readlink(self, path):
        (p,n) = os.path.split(path)
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
        file_max = 0;
        tag_max = 0;
        
        for dirname, dirnames, filenames in os.walk(os.path.join(basepath, "tags")):
            for filename in filenames:
                path = os.path.join(dirname, filename)
                (tmp, tag) = os.path.split(dirname)

                fullpathname = os.path.abspath(os.path.join(dirname, os.readlink(path)))
                if not fullpathname in self.__file_id:
                    file_max += 1
                    file_i = file_max
                    self.__file_id[fullpathname] = file_max
                    self.__id_file[file_i] = fullpathname
                    self.__filename_id[filename] = file_i
                else:
                    file_i = self.__file_id[fullpathname]
                    
                if not tag in self.__tag_id:
                    tag_max += 1
                    tag_i = tag_max
                    self.__tag_id[tag] = tag_i
                    self.__id_tag[tag_i] = tag
                else:
                    tag_i = self.__tag_id[tag]

                if not tag_i in self.__tag_files:
                    self.__tag_files[tag_i] = set()
                self.__tag_files[tag_i].add(file_i)

                if not file_i in self.__file_tags:
                    self.__file_tags[file_i] = set()
                self.__file_tags[file_i].add(tag_i)

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
            tags = self.__findchildtags(set([]))
            for i in tags:
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
    usage='Tag FS ' + fuse.Fuse.fusage
    fs = tagFS(version="%prog " + fuse.__version__,usage=usage,dash_s_do='setsingle')
    fs.parse(errex=1)
    fs.main()

runTagFS()
