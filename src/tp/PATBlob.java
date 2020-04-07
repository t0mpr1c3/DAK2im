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
public class PATBlob extends DAKBlob {
    public PATBlob(File file) throws IOException {
        super(file);
        if (header[0]!='D'||(header[1]!='4'&&header[1]!='6')||header[2]!='C')
            throw new IOException("PAT file header is not D4C or D6C");
    }
    
    private int getFirstDecryptionNumber() {
        return 0;
    }
    
    private String getFirstKeyString() {
        return "00";
    }

    private String getSecondKeyString() {
        return "00";
    }
}
