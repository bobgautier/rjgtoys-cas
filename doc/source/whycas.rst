Why CAS?
========

This CAS is intended to support data backup, in a distributed environment,
where the storage nodes are not completely reliable nor even trustworthy.

Data backup involves storing your data in a (distributed) CAS, along
with metadata such as the original filenames, permissions, etc. of all
the files (as well as their content ids).

Data restore involves finding the metadata and using that to identify
the content to be restored (along with its name, etc.)

The metadata can be stored in any convenient form; it need not be stored
in a CAS itself.  However if the metadata is stored in a CAS, then all
that is needed to retrieve it
is its own content id (and access to a CAS that contains that content item).

When metadata is stored
'internally', in a CAS, the content id of the metadata, and those stored within the metadata
itself form a kind of shallow Merkle Tree http://en.wikipedia.org/wiki/Merkle_tree

The backup scheme for which this CAS was implemented works both with 'internally' stored
metadata and 'externally' stored metadata (that is, stored outside of any CAS, such as
in an ordinary filesystem).

If a collection of metadata is stored in a CAS, only its content id
need be recorded in order to make all the data retrievable.

The content id is of a fixed size, regardless of the size of the data, and is a short(ish)
string that, if not easily memorised, is at least relatively easy to write down.

Once the data itself (including the metadata) is in a suitably robust storage
facility, one way to store the 'backup' for retrieval would be simply to print the
content id on paper and file it.


Because the metadata content id is all that is needed to identify an arbitrary-sized
collection of data (in a tamper-proof way), references to data can be exchanged
easily, for example in (short) emails.


