"""Testing that operations are atomic.

That is, if we have a function that does multiple things,
we want to make sure that if one of those things fails,
the other things are not committed to the database.
"""
