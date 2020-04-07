/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package tp;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;

/**
 * @author t0mpr1c3
 */
public class STPBlob extends DAKBlob {

    public STPBlob(File file) throws IOException {
        super(file);
        if (header[0]!='D'||header[1]!='7'||header[2]!='c')
            throw new IOException("STP file header is not D7c");
    }
    
    public byte[] getPatternXorKey() {
        if (!haveXorKey) {
            String key=getSecondKeyString();
            int val=getSecondDecryptionNumber();
            xorKey=new byte[maxXorLength];
            for (int i=0; i<maxXorLength; i++) {
                int index=(((i+1)%key.length()));
                byte temp1=(byte)key.charAt(index);
                byte temp2=(byte)((val%(i+1))&0xff);
                xorKey[i]=(byte)(temp1^temp2);
            }
            haveXorKey=true;
        }
        return xorKey;
    }

    private int getFirstDecryptionNumber() {
        if (!haveFirstDecryptionNumber) {
            int temp;
            firstDecryptionNumber=getDwordAt(0x35)/2; debug(firstDecryptionNumber);
            temp=getWordAt(0x3f)*4;                   debug(temp); firstDecryptionNumber+=temp; debug(firstDecryptionNumber);
            temp=getDwordAt(0x39);                    debug(temp); firstDecryptionNumber+=temp; debug(firstDecryptionNumber);
            temp=getWordAt(0x3d);                     debug(temp); firstDecryptionNumber+=temp; debug(firstDecryptionNumber);
            temp=getByteAt(0x20);                     debug(temp); firstDecryptionNumber+=temp; debug(firstDecryptionNumber);
            haveFirstDecryptionNumber=true;
        }
        return firstDecryptionNumber;
    }
    
    private String getFirstKeyString() {
        if (!haveFirstKeyString) {
            firstKeyString=new String();
            firstKeyString+=getStringAt(0x60);
            firstKeyString+=getStringAt(0x41);
            firstKeyString+=getWordAt(0x3d);
            firstKeyString+=getByteAt(0x20);
            firstKeyString+=getStringAt(0x41);
            firstKeyString+=getByteAt(0x20);
            firstKeyString+=getWordAt(0x3d);
            debug("First Key String", firstKeyString);
            haveFirstKeyString=true;
        }
        return firstKeyString;
    }

    private int getSecondDecryptionNumber() {
        if (!haveSecondDecryptionNumber) {
            int salt1=getWordAt(0x39);
            int salt2=(getWordAt(0x35)&0xfff)>0 ? 1 : 0;
            secondDecryptionNumber=getFirstDecryptionNumber();
            String tempString=getFirstKeyString();
            for (int i=0; i<tempString.length(); i++) {
                byte b=(byte)(tempString.charAt(i)/2);
                switch (i%3) {
                    // Warning: The original disassembly has these 1-indexed, as
                    // they use pascal strings there. We use 0-indexed. So be
                    // careful when comparing these case statements to the original
                    // ones.
                    case 0:
                        int temp=b/5*getWordAt(0x3f);
                        secondDecryptionNumber+=(i+1)*salt2;
                        secondDecryptionNumber+=b*6;
                        secondDecryptionNumber+=temp;
                        debug("after type 0", secondDecryptionNumber);
                        break;
                    case 1:
                        secondDecryptionNumber+=(i+1)*salt1;
                        secondDecryptionNumber+=b*4;
                        debug("after type 1", secondDecryptionNumber);
                        break;
                    case 2:
                        temp=(salt2+b)/7;
                        secondDecryptionNumber+=(i+1)*b+temp;
                        debug("after type 2", secondDecryptionNumber);
                        break;
                }
            }
            debug("calculated 2nd number", secondDecryptionNumber);
            haveSecondDecryptionNumber=true;
        }
        return secondDecryptionNumber;
    }
    
    private String getSecondKeyString() {
        if (!haveSecondKeyString) {
            int val=getSecondDecryptionNumber();
            secondKeyString=""+
                    val*3  +
                    val    +
                    val*4  +
                    val*2  +
                    val*5  +
                    val*6  +
                    val*8  +
                    val*7;
            debug("Second Key String", secondKeyString);
            haveSecondKeyString=true;
        }
        return secondKeyString;
    }
}
