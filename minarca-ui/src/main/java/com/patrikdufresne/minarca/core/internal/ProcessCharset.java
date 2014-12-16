package com.patrikdufresne.minarca.core.internal;

import java.io.IOException;
import java.nio.charset.Charset;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.apache.commons.lang3.SystemUtils;

/**
 * Used to get the default charset from process.
 * 
 * @author vmuser
 *
 */
public class ProcessCharset {
    /**
     * Default chartset.
     */
    private static Charset defaultCharset;

    /**
     * Return the default charset used by command line process.
     * 
     * @return
     */
    public static Charset defaultCharset() {
        // Return pre-computed charset
        if (defaultCharset != null) {
            return defaultCharset;
        }
        // For windows
        if (SystemUtils.IS_OS_WINDOWS) {
            // Used chcp command line to get code page
            String codepage = chcp();
            if (codepage != null) {
                codepage = "cp" + codepage;
                if (Charset.isSupported(codepage)) {
                    return defaultCharset = Charset.forName(codepage);
                }
            }
        }
        // Default to default encoding
        return defaultCharset = Charset.defaultCharset();
    }

    /**
     * Execute chcp process.
     * 
     * @return the codpe page or null
     * 
     */
    private static String chcp() {
        try {
            Process p = new ProcessBuilder().command("cmd.exe", "/c", "chcp").redirectErrorStream(true).start();
            StreamHandler sh = new StreamHandler(p, Charset.defaultCharset());
            sh.start();
            if (p.waitFor() != 0) {
                return null;
            }
            // Parse a line similar to
            // Page de codes active : 850
            String output = sh.getOutput();
            Matcher m = Pattern.compile("[0-9]+").matcher(output);
            if (!m.find()) {
                return null;
            }
            return m.group(0);
        } catch (IOException e) {
            // Swallow
            e.printStackTrace();
        } catch (InterruptedException e) {
            // Swallow. Should no happen
            Thread.currentThread().interrupt();
        }
        return null;
    }
}
