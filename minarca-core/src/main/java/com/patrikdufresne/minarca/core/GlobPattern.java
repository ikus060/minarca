/*
 * Copyright (C) 2020, IKUS Software inc. All rights reserved.
 * IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.file.FileSystems;
import java.nio.file.PathMatcher;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;

import org.apache.commons.io.output.FileWriterWithEncoding;
import org.apache.commons.lang3.SystemUtils;
import org.apache.commons.lang3.Validate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.internal.Compat;

/**
 * Instance of this class represent a globing pattern for include or exclude.
 * 
 * @author Patrik Dufresne
 * @see http://www.nongnu.org/rdiff-backup/rdiff-backup.1.html
 */
public class GlobPattern {

    /**
     * List of advance patterns
     */
    public static final List<GlobPattern> ADVANCE_BEFORE;

    /**
     * List of advance pattern
     */
    public static final List<GlobPattern> ADVANCE_AFTER;

    /**
     * List of default patterns
     */
    public static final List<GlobPattern> DEFAULTS;

    private static final transient Logger LOGGER = LoggerFactory.getLogger(GlobPattern.class);

    static {
        List<GlobPattern> patterns = new ArrayList<GlobPattern>();
        patterns.addAll(readResource("default"));
        // Filter out.
        List<GlobPattern> list = new ArrayList<GlobPattern>();
        for (GlobPattern p : patterns) {
            if (p.isFileExists() || p.isGlobbing()) {
                list.add(p);
            }
        }
        DEFAULTS = list;
    }

    static {
        ADVANCE_BEFORE = readResource("advance_before");
        ADVANCE_AFTER = readResource("advance_before");
    }

    private static String encode(String pattern) {
        return pattern.replace("\\", "/");
    }

    /**
     * Replace ${} by real value.
     * 
     * @param value
     * 
     * @return
     */
    private static String expand(String value) {
        return value
                .replace("${home}", SystemUtils.USER_HOME)
                .replace("${user.home}", SystemUtils.USER_HOME)
                .replace("${log.folder}", Compat.LOG_FOLDER)
                .replace("${root}", Compat.getRootsPath()[0].toString())
                .replace("${temp}", Compat.TEMP);
    }

    private static String getPath(File file) {
        return file.getAbsolutePath();
    }

    /**
     * True if the pattern is advance.
     * 
     * @param pattern
     * @return
     */
    public static boolean isAdvance(GlobPattern pattern) {
        return ADVANCE_AFTER.contains(pattern) || ADVANCE_BEFORE.contains(pattern);
    }

    private static boolean isGlobbing(String pattern) {
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
        try {
            return readPatterns(reader);
        } finally {
            reader.close();
        }
    }

    private static List<GlobPattern> readPatterns(Reader reader) throws IOException {
        BufferedReader buf = new BufferedReader(reader);
        List<GlobPattern> list = new ArrayList<GlobPattern>();
        String line;
        while ((line = buf.readLine()) != null) {
            if (line.startsWith("#")) {
                continue;
            }
            if (!line.startsWith("+") && !line.startsWith("-")) {
                LOGGER.warn("invalid pattern [{}] discarded", line);
                continue;
            }
            boolean include = line.startsWith("+");
            try {
                list.add(new GlobPattern(include, line.substring(1)));
            } catch (IllegalArgumentException e) {
                // Swallow
                LOGGER.warn("invalid pattern [{}] discarded", line);
            }
        }
        return list;
    }

    /**
     * Search a resource.
     * 
     * @param location
     * @return
     * @throws IOException
     */
    private static List<GlobPattern> readResource(String location) {
        LOGGER.trace("read glob pattern from [{}]", location);
        List<String> locations = new ArrayList<String>();
        locations.add(location);
        // Add OS name.
        String osname = SystemUtils.OS_NAME.replaceAll("\\s", "").trim().toLowerCase();
        if (osname.contains("win")) {
            locations.add(location + "_win");
        }
        if (osname != null) {
            locations.add(location + "_" + osname);
        }
        // Add local
        String lang = Locale.getDefault().getLanguage();
        if (lang != null) {
            locations.add(location + "_" + lang);
            if (osname != null) {
                locations.add(location + "_" + osname + "_" + lang);
            }
        }

        LinkedHashSet<GlobPattern> list = new LinkedHashSet<GlobPattern>();
        for (String l : locations) {
            LOGGER.trace("try to load glob pattern from [{}]", l);
            InputStream in = GlobPattern.class.getResourceAsStream(l);
            if (in == null) {
                continue;
            }
            LOGGER.trace("reading glob pattern from [{}]", l);
            try {
                try {
                    for (GlobPattern p : readPatterns(new InputStreamReader(in))) {
                        p = new GlobPattern(p.isInclude(), expand(p.value()));
                        list.add(p);
                    }
                } finally {
                    in.close();
                }
            } catch (IOException e) {
                LOGGER.error("fail to read patterns", e);
            }
        }

        return new ArrayList<GlobPattern>(list);
    }

    /**
     * Internal method used to write the patterns into a file.
     * 
     * @param file
     * @param pattern
     * @throws IOException
     */
    public static void writePatterns(File file, List<GlobPattern> pattern) throws IOException {
        FileWriterWithEncoding writer = Compat.openFileWriter(file, Compat.CHARSET_DEFAULT);
        for (GlobPattern line : pattern) {
            writer.append(line.isInclude() ? "+" : "-");
            writer.append(line.value());
            writer.append(SystemUtils.LINE_SEPARATOR);
        }
        writer.close();
    }

    /**
     * True if glob pattern should be included. False otherwise.
     */
    private final boolean include;

    private transient PathMatcher matcher;

    /**
     * The pattern.
     */
    private final String pattern;

    public GlobPattern(boolean include, File file) {
        this(include, getPath(file));
    }

    /**
     * Create a new glob pattern from a string. This is the default constructor.
     * 
     * @param pattern
     *            the pattern
     */
    public GlobPattern(boolean include, String pattern) {
        Validate.notEmpty(pattern);
        if (!isGlobbing(pattern)) {
            // If not a globing pattern, it should be a real file or directory.
            // Try to get the absolute location of the file.
            File f = new File(pattern);
            if (f.exists()) {
                pattern = f.getAbsolutePath();
            }
        }
        // rdiffweb for windows doesn't support \\ separator, replace them.
        this.include = include;
        this.pattern = encode(pattern);
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;
        if (obj == null) return false;
        if (getClass() != obj.getClass()) return false;
        GlobPattern other = (GlobPattern) obj;
        if (include != other.include) return false;
        if (pattern == null) {
            if (other.pattern != null) return false;
        } else if (!pattern.equals(other.pattern)) return false;
        return true;
    }

    @Override
    public int hashCode() {
        final int prime = 31;
        int result = 1;
        result = prime * result + (include ? 1231 : 1237);
        result = prime * result + ((pattern == null) ? 0 : pattern.hashCode());
        return result;
    }

    /**
     * True if the pattern matches an existing file.
     * 
     * @return
     */
    public boolean isFileExists() {
        File f = new File(this.value());
        return f.exists();
    }

    /**
     * True if the pattern contains any globbing character to be expended.
     * 
     * @return
     */
    public boolean isGlobbing() {
        return isGlobbing(this.pattern);
    }

    /**
     * True if the glob pattern include the given pattern.
     * 
     * @return
     */
    public boolean isInclude() {
        return this.include;
    }

    /**
     * Check if the current pattern matches the given root.
     * 
     * @param root
     * @return Return True if the pattern may be applied to the given root.
     */
    public boolean isInRoot(File root) {
        return this.toString().startsWith(root.toString());
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
        String path = file.getAbsolutePath();
        if (isGlobbing()) {
            return matcher().matches(Paths.get(path));
        }
        // Do case-sensitive compare (rdiff-backup is case-sensitive on Windows).
        return encode(path).startsWith(this.pattern);
    }

    /**
     * For printing, it's better to use the right file separator.
     */
    @Override
    public String toString() {
        return this.pattern.replace("/", SystemUtils.FILE_SEPARATOR);
    }

    /**
     * The pattern (as required for rdiff-backup).
     * 
     * @return the pattern.
     */
    public String value() {
        return this.pattern;
    }
}
