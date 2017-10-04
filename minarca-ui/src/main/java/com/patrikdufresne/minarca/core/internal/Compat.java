/*
 * Copyright (C) 2015, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core.internal;

import java.io.File;
import java.io.IOException;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.nio.charset.Charset;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import javax.swing.filechooser.FileSystemView;

import org.apache.commons.io.FileUtils;
import org.apache.commons.io.output.FileWriterWithEncoding;
import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.SystemUtils;
import org.apache.commons.lang3.Validate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.APIException;

/**
 * This utility class eases access to OS resources: scheduler, registry, execute process, directory location,
 * permission, access, os charset, etc.
 * 
 * @author Patrik Dufresne
 * 
 */
public class Compat {

    /**
     * Default charset.
     */
    public static final Charset CHARSET_DEFAULT = Charset.defaultCharset();

    /**
     * Charset used for process.
     */
    public static Charset CHARSET_PROCESS;

    /**
     * The name of this computer (may be null in some edge case).
     */
    public static final String COMPUTER_NAME;

    /**
     * Location where to store configuration for minarca.
     */
    public static final String CONFIG_PATH;

    /**
     * The user's home directory.
     */
    public static final String HOME;

    /**
     * The user's home directory.
     */
    public static final File HOME_FILE;

    /**
     * True if the user is admin.
     */
    public static final boolean IS_ADMIN;

    /**
     * Logger used.
     */
    private static final transient Logger LOGGER;

    /**
     * Define temp directory.
     */
    public static final String TEMP;

    /**
     * Define temp directory.
     */
    public static final File TEMP_FILE;

    /**
     * Path to system profile for Windows OS.
     * <p>
     * Under non-windows OS, this constant is null.
     */
    public static final String WINDOWS_SYSTEMPROFILE_PATH;

    static {
        // Use a static block to declare constant value in the right order.
        LOGGER = LoggerFactory.getLogger(Compat.class);
        CHARSET_PROCESS = getProcessCharset();
        COMPUTER_NAME = getComputerName();
        WINDOWS_SYSTEMPROFILE_PATH = getWindowsSystemProfilePath();
        IS_ADMIN = getIsAdmin();
        CONFIG_PATH = getConfigPath(IS_ADMIN);
        TEMP = getTemp();
        TEMP_FILE = new File(TEMP);
        HOME = getHome(IS_ADMIN);
        HOME_FILE = new File(HOME);
    }

    /**
     * Execute chcp process. This command line is used to determine the process charset in Windows OS.
     * 
     * @return the code page or null
     * 
     */
    private static String chcp() {
        try {
            Process p = new ProcessBuilder().command("cmd.exe", "/c", "chcp").redirectErrorStream(true).start();
            StreamHandler sh = new StreamHandler(p, Charset.defaultCharset());
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

    /**
     * Return a computer name to represent this computer.
     * <p>
     * Current implementation gets the hostname from environment variable and use Inet interface to get a hostname.
     * 
     * @return an empty string or a hostname
     */
    private static String getComputerName() {
        // For Windows
        String host = System.getenv("COMPUTERNAME");
        if (host != null) return host.toLowerCase();
        // For Linux
        host = System.getenv("HOSTNAME");
        if (host != null) return host.toLowerCase();
        // Fallback and use Inet interface.
        try {
            String result = InetAddress.getLocalHost().getHostName();
            if (StringUtils.isNotEmpty(result)) return result.toLowerCase();
        } catch (UnknownHostException e) {
            // failed; try alternate means.
        }
        return null;
    }

    /**
     * Return the location of the configuration for minarca when running with admin right.
     * 
     * @return
     */
    private static String getConfigPath(boolean isAdmin) {
        // Check if config path is forced (usually used for testing).
        String configPath = System.getProperty("com.patrikdufresne.minarca.configPath");
        if (configPath != null) {
            return configPath;
        }
        if (SystemUtils.IS_OS_WINDOWS) { // $NON-NLS-1$
            return getLocalAppData(isAdmin) + "/minarca";
        } else if (SystemUtils.IS_OS_LINUX) {
            if (isAdmin) {
                return "/etc/minarca";
            } else {
                return System.getenv("HOME") + "/.config/minarca/";
            }
        }
        return null;
    }

    /**
     * Return user's home.
     * 
     * @param isAdmin
     *            True if admin.
     * @return
     */
    private static String getHome(boolean isAdmin) {
        if (isAdmin) {
            if (SystemUtils.IS_OS_WINDOWS) {
                if (Compat.WINDOWS_SYSTEMPROFILE_PATH == null) {
                    throw new IllegalStateException("system profile path not defined");
                }
                return Compat.WINDOWS_SYSTEMPROFILE_PATH;
            } else {
                return "/root";
            }
        }
        return SystemUtils.USER_HOME;
    }

    /**
     * Return true if the user is admin.
     * <p>
     * This implementation make multiple assumption about administrator right. It checks if user can access the "SYSTEM"
     * registry hive. Can read-write to SYSTEM user profile.
     * 
     * @return
     */
    private static boolean getIsAdmin() {
        // Check if the verification is forced (usually used for testing).
        boolean forceIsAdmin = Boolean.getBoolean("com.patrikdufresne.minarca.isAdmin");
        if (forceIsAdmin) {
            return true;
        }
        if (SystemUtils.IS_OS_WINDOWS_XP) {
            // Query the SYSTEM registry hive.
            try {
                reg("query", "HKU\\S-1-5-18");
            } catch (APIException e) {
                return false;
            }
            // Check if the minarca directory can be created.
            try {
                File file = new File(getConfigPath(true));
                FileUtils.forceMkdir(file);
                if (!file.canRead() || !file.canWrite()) {
                    return false;
                }
            } catch (SecurityException e) {
                return false;
            } catch (IOException e) {
                return false;
            }
            return true;
        } else if (SystemUtils.IS_OS_LINUX) {
            // TODO Need to implements this for linux.
            return false;
        }
        // Otherwise: Windows 7 not running as Admin.
        return false;
    }

    /**
     * Return Local application data (for Windows).
     * 
     * @param isAdmin
     *            True if admin.
     * @return
     */
    private static String getLocalAppData(boolean isAdmin) {
        if (SystemUtils.IS_OS_WINDOWS_XP || SystemUtils.IS_OS_WINDOWS_2003) {
            // C:\Documents and Settings\ikus060\Local Settings\Application Data
            return getHome(isAdmin) + "/Local Settings/Application Data/";
        }
        return getHome(isAdmin) + "/AppData/Local/";
    }

    /**
     * Return the default charset used by command line process.
     * 
     * @return
     */
    private static Charset getProcessCharset() {
        // For windows
        if (SystemUtils.IS_OS_WINDOWS) {
            // Used chcp command line to get code page
            String codepage = chcp();
            if (codepage != null) {
                codepage = "cp" + codepage;
                if (Charset.isSupported(codepage)) {
                    return Charset.forName(codepage);
                }
            }
        }
        // Linux: default to default encoding (usually UTF-8)
        return Charset.defaultCharset();
    }

    /**
     * Return the home drive. On Windows usually return <code>C:\</code>. On linux always return <code>/</code>.
     * 
     * List of roots. On Linux it's always "/". On Windows we may have multiple root "C:\", "D:\", etc.
     * 
     * Do not cache this since this value can changed during runtime on windows.
     * 
     * @return
     */
    public static File[] getRootsPath() {
        FileSystemView fsv = FileSystemView.getFileSystemView();
        List<File> roots = new ArrayList<File>();
        for (File f : File.listRoots()) {
            if (fsv.isFloppyDrive(f)) {
                // Need to exclude floppy.
                continue;
            }
            roots.add(f);
        }
        return roots.toArray(new File[roots.size()]);
    }

    private static String getTemp() {
        // Check if system property return a valid value.
        if (SystemUtils.getJavaIoTmpDir() != null) {
            return SystemUtils.JAVA_IO_TMPDIR;
        }
        // Fall back to TEMP
        String temp = System.getenv("TEMP");
        if (temp != null && temp.length() > 0 && new File(temp).exists()) {
            return temp;
        }
        if (SystemUtils.IS_OS_LINUX) {
            return "/tmp";
        }
        return null;
    }

    /**
     * Return the location of the System profile.
     * 
     * @return Return a directory.
     */
    private static String getWindowsSystemProfilePath() {
        if (SystemUtils.IS_OS_WINDOWS) {
            return System.getenv("WINDIR") + "/System32/config/systemprofile";
        }
        return null;
    }

    /**
     * Open a file as FileWriter with the given encoding.
     * 
     * @param file
     *            the file
     * @param encoding
     *            the encoding to be used to read the file
     * @return the file writer.
     * @throws IOException
     */
    public static FileWriterWithEncoding openFileWriter(File file, String encoding) throws IOException {
        return openFileWriter(file, Charset.forName(encoding));
    }

    /**
     * Open a file as FileWriter with the given encoding.
     * 
     * @param file
     *            the file
     * @param encoding
     *            the encoding to be used to read the file
     * @return the file writer.
     * @throws IOException
     */
    public static FileWriterWithEncoding openFileWriter(File file, Charset encoding) throws IOException {
        if (file.exists()) {
            if (file.isDirectory()) {
                throw new IOException("File '" + file + "' exists but is a directory");
            }
            if (!file.canWrite()) {
                // Try to change permission
                file.setWritable(true, true);
            }
            if (!file.canWrite()) {

                throw new IOException("File '" + file + "' cannot be written to");
            }
        } else {
            File parent = file.getParentFile();
            if (parent != null) {
                if (!parent.mkdirs() && !parent.isDirectory()) {
                    throw new IOException("Directory '" + parent + "' could not be created");
                }
            }
        }
        return new FileWriterWithEncoding(file, encoding);
    }

    /**
     * Execute "reg.exe" with the given arguments.
     * 
     * @param args
     *            the arguments
     * @return the output of the command.
     * @throws APIException
     *             if the process didn't complete successfully.
     */
    private static String reg(String... args) throws APIException {
        List<String> command = new ArrayList<String>();
        command.add("reg.exe");
        if (args != null) {
            command.addAll(Arrays.asList(args));
        }
        LOGGER.debug("executing {}", StringUtils.join(command, " "));
        try {
            Process p = new ProcessBuilder().command(command).redirectErrorStream(true).start();
            StreamHandler sh = new StreamHandler(p);
            if (p.waitFor() != 0) {
                throw new APIException(sh.getOutput());
            }
            return sh.getOutput();
        } catch (IOException e) {
            throw new APIException("fail to create subprocess", e);
        } catch (InterruptedException e) {
            // Swallow. Should no happen
            LOGGER.warn("process interupted", e);
            Thread.currentThread().interrupt();
            return null;
        }
    }

    /**
     * Search for the given filename in multiple locations. Current implementation search in the given
     * <code>paths</code> then search in PATH environment variables.
     * 
     * @param filename
     *            the filename (e.g.: minarca.exe, rdiffweb.exe)
     * @param paths
     *            extra path where to look.
     * 
     * @return the first matching file.
     */
    public static File searchFile(String filename, String... paths) {
        Validate.notEmpty(filename);
        Validate.notNull(paths);
        List<String> locations = new ArrayList<String>();
        locations.addAll(Arrays.asList(paths));
        locations.add(".");
        // Add PATH location.
        String path = System.getenv("PATH");
        if (path != null) {
            for (String i : path.split(SystemUtils.PATH_SEPARATOR)) {
                locations.add(i);
            }
        }
        for (String location : locations) {
            if (location == null || location.isEmpty()) {
                continue;
            }
            File file = new File(location, filename);
            if (file.isFile() && file.canRead()) {
                try {
                    return file.getCanonicalFile();
                } catch (IOException e) {
                    LOGGER.warn("fail to get canonical path for [{}]", file);
                    return null;
                }
            }
        }
        return null;
    }
}
