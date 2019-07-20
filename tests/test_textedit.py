from __future__ import absolute_import, unicode_literals, print_function

import unittest

# A TextEdit is a new CRDT similar to a list in some ways but designed for
# storing collaboratively edited text files. The problem it solves is -
# we could implement a text edit as a List of characters but that is
# unduely slow for fairly large files. A test of inserted 100,000 characters
# in such an array took 38 seconds. So for example importing an existing
# source code file. This data is designed to handle these large copy paste type
# edit much more easily.
#
# Algorithm notes
# Text is an array of fragments.
#
# Each fragment is a string of text. Once a fragment is produced it can never
# be changed (but it can be replaced)
#
# The text fragment also caches it's current index into the output. When a new
# fragment is inserted every fragment after it must be moved along.
#
# When a fragment is deleted fragments after it are moved back.
#
# When we insert we can easily go from the current index into the string to which ever fragment we are in because we can then perform a binary search thru the list.
#
# Each fragment has a few operations
# Split which will remove a fragment and replace it which two other ones
# Insert new fragment - this inserts a new fragment and moves everything else around
# Delete a fragment - remove it from the current list. This tombstones it since we can never fully delete.
#
# In the future we will need to calculate line begining and put them into this list.
#
# This work is inspired by y.js, concave and atom teletype-crdt. But not based
# on any of their algorithms
#
# Future evolution:
# Stage one is to get this to work as outlined for simple text editing
# Stage two add support for markers (as per atom teletype)
# Stage three a new related datatype for rich text editing
#
