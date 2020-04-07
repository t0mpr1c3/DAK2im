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
public class ReadDAK {

    /**
     * @param args the command line arguments
     */
    public static void main(String[] args) throws IllegalArgumentException, IOException {
        String filename;
        if (args.length>=1)
            filename=args[0];
        else {
            filename="";
            throw new IllegalArgumentException("Filename required");
        }
        DAKReader reader=new DAKReader(filename);
        reader.read();
    }
}