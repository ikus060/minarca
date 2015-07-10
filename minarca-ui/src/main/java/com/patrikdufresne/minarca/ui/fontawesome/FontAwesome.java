package com.patrikdufresne.minarca.ui.fontawesome;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;

import org.apache.commons.io.IOUtils;
import org.eclipse.jface.resource.JFaceResources;
import org.eclipse.swt.SWT;
import org.eclipse.swt.graphics.Font;
import org.eclipse.swt.graphics.FontData;
import org.eclipse.swt.widgets.Display;

/**
 * Utility class used to load the font awesome font.
 * 
 * @author Patrik Dufresne
 * 
 */
public class FontAwesome {

    /**
     * Symbolic name used to store the font awesome.
     */
    public static final String FONTAWESOME = "FONTAWESOME";

    public static final String QUESTION_CIRCLE = "\uf059";

    public static final String INFO = "\uf129";

    public static final String QUESTION = "\uf128";

    public static final String PLUS = "\uf067";

    public static String TIMES = "\uf00d";

    /**
     * Load the font from resources.
     * 
     * @return
     */
    private static boolean loadFont() {
        // Get file from classpath.
        InputStream in = FontAwesome.class.getResourceAsStream("fontawesome-webfont.ttf");
        if (in == null) {
            return false;
        }

        File tempfile;
        try {
            tempfile = File.createTempFile("swt-", "-fontawesome-webfont.ttf");
            FileOutputStream out = new FileOutputStream(tempfile);
            try {
                IOUtils.copy(in, out);
            } finally {
                out.close();
            }
            tempfile.deleteOnExit();
        } catch (IOException e) {
            return false;
        }

        return Display.getDefault().loadFont(tempfile.getAbsolutePath());
    }

    /**
     * Return SWT font.
     * 
     * @return the font or null.
     */
    public static Font getFont() {
        if (JFaceResources.getFontRegistry().hasValueFor(FONTAWESOME)) {
            return JFaceResources.getFontRegistry().get(FONTAWESOME);
        }
        if (!loadFont()) {
            return null;
        }
        FontData[] data = new FontData[] { new FontData("fontawesome", 14, SWT.NORMAL) };
        JFaceResources.getFontRegistry().put(FONTAWESOME, data);
        return JFaceResources.getFontRegistry().get(FONTAWESOME);
    }
}
