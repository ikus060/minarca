/*
 * Copyright (c) 2014, Patrik Dufresne Service Logiciel. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.file.FileSystems;
import java.nio.file.PathMatcher;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

import org.apache.commons.io.output.FileWriterWithEncoding;
import org.apache.commons.lang3.SystemUtils;
import org.jsoup.helper.Validate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.internal.Compat;

/**
 * Instance of this class represent a globbing pattern for include or exclude.
 * 
 * @author Patrik Dufresne
 * @see http://www.nongnu.org/rdiff-backup/rdiff-backup.1.html
 */
public class GlobPattern {

    private static final transient Logger LOGGER = LoggerFactory.getLogger(GlobPattern.class);

    private static String encode(String pattern) {
        return pattern.replace("\\", "/");
    }

    private static String getPath(File file) {
        try {
            return file.getCanonicalPath();
        } catch (IOException e) {
            return file.getAbsolutePath();
        }
    }

    public static boolean isGlobbing(String pattern) {
        return pattern.contains("*") || pattern.contains("?");
    }

    /**
     * Internal method used to read patterns.
     * 
     * @param file
     * @return
     * @throws IOException
     */
    public static List<GlobPattern> readPatterns(File file) throws IOException {
        FileInputStream in = new FileInputStream(file);
        BufferedReader reader = new BufferedReader(new InputStreamReader(in, Compat.CHARSET_DEFAULT));
        List<GlobPattern> list = new ArrayList<GlobPattern>();
        String line;
        while ((line = reader.readLine()) != null) {
            if (line.startsWith("#")) {
                continue;
            }
            try {
                list.add(new GlobPattern(line));
            } catch (IllegalArgumentException e) {
                // Swallow
                LOGGER.warn("invalid pattern [{}] discarded", line);
            }
        }
        reader.close();
        return list;
    }

    /**
     * Internal method used to write the patterns into a file.
     * 
     * @param file
     * @param pattern
     * @throws IOException
     */
    public static void writePatterns(File file, List<GlobPattern> pattern) throws IOException {
        FileWriterWithEncoding writer = new FileWriterWithEncoding(file, Compat.CHARSET_DEFAULT);
        for (GlobPattern line : pattern) {
            writer.append(line.value());
            writer.append(SystemUtils.LINE_SEPARATOR);
        }
        writer.close();
    }

    private PathMatcher matcher;

    /**
     * The pattern.
     */
    private final String pattern;

    public GlobPattern(File file) {
        this(getPath(file));
    }

    /**
     * Create a new glob pattern from a string. This is the default constructor.
     * 
     * @param pattern
     *            the pattern
     */
    public GlobPattern(String pattern) {
        Validate.notEmpty(pattern);
        if (!isGlobbing(pattern)) {
            // If not a globbing pattern, it should be a real file or directory.
            // Try to get the absolute location of the file.
            File f = new File(pattern);
            if (f.exists()) {
                try {
                    pattern = f.getCanonicalPath();
                } catch (IOException e) {
                    // Swallow exception. Keep original pattern.
                }
            }
        }
        // rdiffweb for windows doesn't support \\ separator, replace them.
        this.pattern = encode(pattern);
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;
        if (obj == null) return false;
        if (getClass() != obj.getClass()) return false;
        GlobPattern other = (GlobPattern) obj;
        if (pattern == null) {
            if (other.pattern != null) return false;
        } else if (!pattern.equals(other.pattern)) return false;
        return true;
    }

    @Override
    public int hashCode() {
        final int prime = 31;
        int result = 1;
        result = prime * result + ((pattern == null) ? 0 : pattern.hashCode());
        return result;
    }

    /**
     * True if the pattern contains any globbing character to be expended.
     * 
     * @return
     */
    public boolean isGlobbing() {
        return isGlobbing(this.pattern);
    }

    private PathMatcher matcher() {
        if (this.matcher != null) {
            return this.matcher;
        }
        return this.matcher = FileSystems.getDefault().getPathMatcher("glob:" + this.pattern);
    }

    /**
     * Check if the given pattern matches the given filename.
     * 
     * @param file
     * @return
     */
    public boolean matches(File file) {
        // Try to get canonical name.
        String path;
        try {
            path = file.getCanonicalPath();
        } catch (IOException e) {
            path = file.getAbsolutePath();
        }
        if (isGlobbing()) {
            return matcher().matches(Paths.get(path));
        }
        return encode(path).startsWith(this.pattern);

    }

    @Override
    public String toString() {
        return this.pattern.replace("/", "\\");
    }

    public String value() {
        return this.pattern;
    }
}
