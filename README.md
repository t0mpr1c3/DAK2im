# DAKReader

This is a small Python3 program used to explore the contents of Designaknit .stp and .pat files, which are used for knitting patterns. The code for .stp files was originally written in Java by Guntram Blohm in response to a stackexchange question (https://reverseengineering.stackexchange.com/questions/12235/reading-stp-designaknit-stitch-pattern-files-ii/12239#12239).

As .stp files are somewhat encrypted, it's not easily possible to read or convert them to anything else. 
The original intention of this software was to show how to read and decrypt those files. The older .pat file format is similar but without any encryption.

The program reads two kinds of data from the files:

* color pattern
* color palette

Two further types of information are ignored, for the current purposes:

* stitch pattern
* stitch types

The __main__() method demonstrates the DAKReader class by opening a .pat or .stp file and writing the color pattern to a .png file.