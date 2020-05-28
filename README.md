# DAKimport

This is a small Python3 module to import Designaknit .stp and .pat knitting pattern files as images. The code to convert .stp files was originally written in Java by Guntram Blohm in response to a stackexchange question (https://reverseengineering.stackexchange.com/questions/12235/reading-stp-designaknit-stitch-pattern-files-ii/12239#12239).

As .stp files are somewhat encrypted, it's not easily possible to read or convert them to anything else. 
The original intention of this software was to show how to read and decrypt those files. The older .pat file format is similar but without any encryption.

The program reads two kinds of data from the files:

* color pattern
* color palette

Two further types of information are ignored, for the current purposes:

* stitch pattern
* stitch types

The two public methods of the Importer class are pat2im() and stp2im(). They take as their argument a filename and return a PIL.Image object. 
