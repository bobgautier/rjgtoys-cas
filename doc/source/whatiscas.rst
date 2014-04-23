What is CAS?
============

According to Wikipedia, a CAS ('Content Addressable Storage') is 'a mechanism for storing information that can be
retrieved based on its content, not its storage location' http://en.wikipedia.org/wiki/Content-addressable_storage

This implementation, like many others, works by using hashes of the content as addresses.   The use of hashes is
justified on the grounds that a hash of some data
is (usually) smaller than the data itself, and that the probability of two different pieces of content producing the
same hash is negligible.

For me there is a third good reason for using hashes as addresses: it makes the data tamper-proof.   On retrieving a
piece of data it's pretty easy to check that the data you got has the hash you originally presented.   Consequently,
there is no need to trust storage nodes completely; you will be able to detect damage and/or tampering.

