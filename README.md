# Prerequisites

To run pytagfs you need
* python-2.x (2.7 is preferred)
* fuse-python module (see http://pypi.python.org/pypi/fuse-python/)
* linux fuse installed (2.9 is preferred)

# Installation

If you want to give the pytagfs a try clone the git repository first.
<pre>
~/code $ git clone https://github.com/dizel-by/pytagfs.git
</pre>
Next cd to the pytagfs directory...
<pre>
~/code $ cd pytagfs
</pre>
and create a mountpoint directory inside.
<pre>
~/code/pytagfs $ mkdir mountpoint
</pre>
Good, now mount the pytagfs.
<pre>
~/code/pytagfs $ python tags.py test/ mountpoint/
</pre>
This should end fine. Now you have pytagfs mounted to mountpoint/, read on.

# Usage

First cd to the mountpoint/ directory.
<pre>
~/code/pytagfs $ cd mountpoint/
</pre>
Now if you followed the Installation instructions above you should see a list of tag directories in mountpoint/
<pre>
~/code/pytagfs/mountpoint $ ls -F
tag1/  tag2/  tag3/  tag4/

~/code/pytagfs/mountpoint $ ls -F tag1/
file1@  file2@  tag3/  tag4/

~/code/pytagfs/mountpoint $ readlink tag1/file1
/home/ivan/code/pytagfs/test/file1
</pre>
As you can see each tag directory contains links to actual files and other tags these files are tagged with.
If you remove a link pytagfs adjusts the tags automagically.
<pre>
~/code/pytagfs/mountpoint $ ls -F tag1/ tag3/
tag1/:
file1@  file2@  tag3/  tag4/

tag3/:
file1@  tag1/  tag4/

~/code/pytagfs/mountpoint $ rm tag1/file1

~/code/pytagfs/mountpoint $ ls -F tag1/ tag3/
tag1/:
file2@  tag4/

tag3/:
</pre>
You can see what's going on by checking the test/ directory insides (I'll use git status).
<pre>
~/code/pytagfs/mountpoint $ (cd .. && git status -s)
 D test/tags/tag1/file1
 D test/tags/tag3/file1
 D test/tags/tag4/file1
</pre>

Ok then, now I'm going to add a tag and then tag an existing file.
<pre>
~/code/pytagfs/mountpoint $ mkdir textfiles

~/code/pytagfs/mountpoint $ ls -F
tag1/  tag2/  tag3/  tag4/  textfiles/

~/code/pytagfs/mountpoint $ ln -s $(realpath ../test/file1) textfiles/

~/code/pytagfs/mountpoint $ ls -F textfiles/
file1@
</pre>
And obviously.
<pre>
~/code/pytagfs/mountpoint $ readlink textfiles/file1 
/home/ivan/code/pytagfs/test/file1
</pre>
And under the hood (I'll ignore old, now irrelevant output starting now).
<pre>
~/code/pytagfs/mountpoint $ (cd .. && git add test/tags/textfiles/ && git status -s)
A  test/tags/textfiles/file1
</pre>
I had to git-add because git doesn't care about directories it wasn't asked to watch.

And I'm going to add a file now.
<pre>
~/code/pytagfs/mountpoint $ echo 'Roses are red.' > ../test/poetry

~/code/pytagfs/mountpoint $ ln -s $(realpath ../test/poetry) textfiles/

~/code/pytagfs/mountpoint $ ls -F textfiles/
file1@  poetry@

~/code/pytagfs/mountpoint $ readlink textfiles/poetry 
/home/ivan/code/pytagfs/test/poetry
</pre>
There are two things I want to say here. Firstly the $(realpath) thingie, we don't support relpath targets. And secondly, note that pytagfs works with symlinks and doesn't store the actual files, that's why I had to create a file in test/poetry first and then symlink it. But I'm going to try it nevertheless.
<pre>
~/code/pytagfs/mountpoint $ echo text > textfiles/newfile
bash: textfiles/newfile: Function not implemented

~/code/pytagfs/mountpoint $ ls -F textfiles/
file1@  poetry@
</pre>
Oops.

One last thing, I'll get a list of files tagged with both tag1 and tag4.
<pre>
~/code/pytagfs/mountpoint $ ls -F tag1/tag4/
file2@

~/code/pytagfs/mountpoint $ ls -F tag4/tag1/
file2@
</pre>
Ok, now unmount.
<pre>
~/code/pytagfs/mountpoint $ cd .. && fusermount -u mountpoint/
</pre>
And we're done. Here is what git status shows me.
<pre>
~/code/pytagfs $ git status -s
 D test/tags/tag1/file1
 D test/tags/tag3/file1
 D test/tags/tag4/file1
A  test/tags/textfiles/file1
?? test/poetry
?? test/tags/textfiles/poetry
</pre>

# Hacking

For playing with fuse-python you will need this link: http://sourceforge.net/apps/mediawiki/fuse/index.php?title=FUSE_Python_Reference

Then we have TagFS.__log(s) for appending strings to /tmp/tags.log file. ls does readdir() (and bash getattr() for every thing it sees to determine how to display it), rm calls unlink(). symlink(), mkdir() and rmdir() are pretty much self-explanatory.

Have fun.

