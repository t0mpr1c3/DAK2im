/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package tp;

import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import javax.imageio.ImageIO;

/**
 * @author gbl, t0mpr1c3
 */
public class DAKReader {

    private String filename;
    private DAKBlob blob;

    public DAKReader(String filename) throws IllegalArgumentException, IOException {
        this.filename=filename;
        this.blob=makeBlob();
    }

    public DAKBlob makeBlob() throws IllegalArgumentException, IOException {
        int dot=filename.lastIndexOf('.');
        String suffix=filename.substring(dot+1,filename.length());
        Boolean stp=suffix.equals("stp");
        Boolean pat=suffix.equals("pat");
        File file=new File(filename);
        if (stp)
            return new STPBlob(file);
        else if (pat)
            return new PATBlob(file);
        else
            throw new IllegalArgumentException("Filename must have .stp or .pat suffix");
    }

    public void read() {
        blob.setDebugging(false);
        System.out.println("Stitch color map");
        byte[] pixels=blob.getDataBlock1Pixels(blob.getPatternXorKey());
        int pos;
        for (int i=0; i<blob.getHeight(); i++) {
            pos=(blob.getHeight()-i-1)*blob.getWidth();
            for (int j=0; j<blob.getWidth(); j++)
                System.out.print((char)pixels[pos++]);
            System.out.println();
        }
        System.out.println("Color map");
        for (int i=32; i<75; i++) {
            System.out.println("'"+(char)i+"': "+blob.getColor(i,blob.getPatternXorKey()).toString());
        }
        System.out.println("Stitch type map, decoding not completed");
        pixels=blob.getDataBlock2Pixels(blob.getPatternXorKey());
        for (int i=0; i<blob.getHeight(); i++) {
            pos=(blob.getHeight()-i-1)*blob.getWidth();
            for (int j=0; j<blob.getWidth(); j++) 
                System.out.print((char)pixels[pos++]);
            System.out.println();
        }
        BufferedImage canvas=new BufferedImage(blob.getWidth(), blob.getHeight(), BufferedImage.TYPE_3BYTE_BGR);
        pixels=blob.getDataBlock1Pixels(blob.getPatternXorKey());
        for (int i=0; i<blob.getWidth(); i++) {
            for (int j=0; j<blob.getHeight(); j++) {
                int pixelPos = (blob.getHeight()-j-1)*blob.getWidth()+i;
                int pixel = pixels[pixelPos];
                DAKColor color = blob.getColor(pixel,blob.getPatternXorKey());
                canvas.setRGB(i, j, color.getR()<<16 | color.getG()<<8 | color.getB());
            }
        }
        File outputFile=new File(filename.substring(0, filename.length()-4)+".png");
        if (!outputFile.exists()) {
            try {
                ImageIO.write(canvas, "png", outputFile);
            } catch (IOException ex) {
                System.err.println(ex);
            }
        } else {
            System.err.println("will not overwrite existing file "+outputFile.getName());
        }
    }
}
