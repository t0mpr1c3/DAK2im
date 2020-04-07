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
 * @author gbl
 */
public abstract class DAKBlob {
    protected int maxXorLength=21000;
    protected int length;
    protected byte data[];
    protected byte header[];
    protected boolean debugging;
    protected List<DAKVarLenDataBlock> firstBlocks, secondBlocks;
    protected boolean dataBlocksInitialized;
    protected boolean haveFirstDecryptionNumber;  protected int firstDecryptionNumber;
    protected boolean haveFirstKeyString;         protected String firstKeyString;
    protected boolean haveSecondDecryptionNumber; protected int secondDecryptionNumber;
    protected boolean haveSecondKeyString;        protected String secondKeyString;
    protected boolean haveXorKey;                 protected byte xorKey[];
    protected int paletteStart;
    protected int paletteRemap;
    
    public DAKBlob(File file) throws IOException {
        this.length=(int) file.length();
        this.data=new byte[length];
        this.dataBlocksInitialized=false;
        this.debugging=false;
        this.haveFirstDecryptionNumber=false;
        this.haveFirstKeyString=false;
        this.haveSecondDecryptionNumber=false;
        this.haveSecondKeyString=false;
        this.haveXorKey=false;
        try (InputStream reader=new FileInputStream(file)) {
            this.header=readHeader(reader);
            int pos=3, n;
            while (pos<length) {
                n=reader.read(data, pos, this.length-pos);
                if (n<=0) {
                    System.out.printf("length %d\n", this.length);
                    System.out.printf("pos %d\n", pos);
                    throw new IOException("End of File reached before reading enough bytes");
                }
                pos+=n;
            }
        } catch (FileNotFoundException ex) {
            throw(ex);
        }
    }
    
    public void setDebugging(boolean b) {
        debugging=b;
    }
    
    public int getHeight() {
        return getWordAt(5);
    }
    
    public int getWidth() {
        return getWordAt(3);
    }

    public byte[] readHeader(InputStream f) throws IOException {
        byte[] header=new byte [3];
        int headerRead=f.read(header,0,3);
        return header;
    }
    
    protected int getByteAt(int pos) {
        return (data[pos]&0xff);
    }
    
    protected int getWordAt(int pos) {
        return getByteAt(pos) | (getByteAt(pos+1)<<8);
    }
    
    protected int getDwordAt(int pos) {
        return getByteAt(pos) |
                (getByteAt(pos+1)<<8) |
                (getByteAt(pos+2)<<16) |
                (getByteAt(pos+3)<<24);
    }
    
    /* Pascal strings! */
    protected String getStringAt(int pos) {
        int size=getByteAt(pos);
        char[] chars=new char[size];
        for (int i=0; i<size; i++) {
            chars[i]=(char) getByteAt(pos+i+1);
        }
        return new String(chars);
    }
    
    public void debug(int val) { if (debugging) System.out.println(Integer.toHexString(val)); }
    public void debug(String s, int val) { if (debugging) System.out.println(s+": "+Integer.toHexString(val)); }
    public void debug(String s, String t) { if (debugging) System.out.println(s+": "+t); }    

    protected void initDataBlocks(byte[] key) {
        if (!dataBlocksInitialized) {
            int startPos=0xf8;
            DAKVarLenDataBlock nextBlock;
            firstBlocks=new ArrayList<>();
            secondBlocks=new ArrayList<>();
            do {
                nextBlock=new DAKVarLenDataBlock(data, startPos, key);
                firstBlocks.add(nextBlock);
                if (debugging) {
                    System.out.println("Block at "+Integer.toHexString(startPos)+
                        " height "+nextBlock.getHeight()+" has "+
                            Integer.toHexString(nextBlock.getNbytes())+" bytes, "+
                            "next start at "+Integer.toHexString(startPos+nextBlock.getNbytes()+4)
                        );
                }
                startPos+=nextBlock.getNbytes()+4;
            } while (nextBlock.getHeight()!=this.getHeight());
            do {
                nextBlock=new DAKVarLenDataBlock(data, startPos, key);
                secondBlocks.add(nextBlock);
                if (debugging) {
                    System.out.println("Block at "+Integer.toHexString(startPos)+
                        " height "+nextBlock.getHeight()+" has "+
                            Integer.toHexString(nextBlock.getNbytes())+" bytes, "+
                            "next start at "+Integer.toHexString(startPos+nextBlock.getNbytes()+4)
                        );
                }
                startPos+=nextBlock.getNbytes()+4;
            } while (nextBlock.getHeight()!=this.getHeight());
            paletteStart=startPos;  debug("Palette starts at", paletteStart); startPos+=1775;
            paletteRemap=startPos;  debug("Palette remap  at", paletteRemap);
            dataBlocksInitialized=true;
        }
    }

    protected void decodeRLEData(byte[] pixels, List<DAKVarLenDataBlock>blocks,
            int height, int width, int remapStart) {
        debug("height", height);
        debug("width", width);
        int pixelRowStart=0;
        int blockno=0;
        int posInData=0;
        int posOutData=0;
        byte[] inputData=blocks.get(0).getData();
        debug("pixels length",pixels.length);
        debug("input length",inputData.length);
        for (int row=0; row<height; row++) {
            if (row==blocks.get(blockno).getHeight()) {
                inputData=blocks.get(++blockno).getData();
                posInData=0;
            }
            for (int col=0; col<width; ) {
                byte b=inputData[posInData++];
                int  len=1;
                if ((b&0x80)!=0) {
                    len=b&0x7f;
                    b=inputData[posInData++];
                }
                if (remapStart!=0) {
                    b=this.data[remapStart+b*2-2];
                }
                for (int i=0; i<len; i++) {
                    pixels[posOutData++]=b;
                }
                col+=len;
            }
        }
    }
    
    public byte[] getPatternXorKey() {
        return null;
    }
    
    public DAKColor getColor(int index, byte[] key) {
        initDataBlocks(key);
        return new DAKColor(data, paletteStart+index*25);
    }

    public byte[] getDataBlock1Pixels(byte[] key) {
        byte[] pixels=new byte[getWidth()*getHeight()];
        initDataBlocks(key);
        decodeRLEData(pixels, firstBlocks, getHeight(), getWidth(), 0);
        return pixels;
    }

    public byte[] getDataBlock2Pixels(byte[] key) {
        byte[] pixels=new byte[getWidth()*getHeight()];
        initDataBlocks(key);
        decodeRLEData(pixels, secondBlocks, getHeight(), getWidth(), paletteRemap);
        return pixels;
    }
}
