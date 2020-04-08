# DAKReader

This is a small Python3 module used to explore the contents of Designaknit .stp and .pat files, which are used for knitting patterns. The code for .stp files was originally written in Java by Guntram Blohm in response to a stackexchange question (https://reverseengineering.stackexchange.com/questions/12235/reading-stp-designaknit-stitch-pattern-files-ii/12239#12239).

As .stp files are somewhat encrypted, it's not easily possible to read or convert them to anything else. 
The original intention of this software was to show how to read and decrypt those files. The older .pat file format is similar but without any encryption.

The program reads three kinds of data from the files:

* stitch patterns
* colors
* stitch types

and writes the color pattern to a .png file.

The information on stitch types may not be correctly encoded. I have not yet seen any data files containing information of this kind that I can cross-refer to another source of information, such as a written knitting pattern or chart.