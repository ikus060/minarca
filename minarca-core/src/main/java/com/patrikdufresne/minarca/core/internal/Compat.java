/*
 * Copyright (C) 2019, Patrik Dufresne Service Logiciel inc. All rights reserved.
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
import java.util.Map.Entry;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

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
     * 
     * <pre>
     * $HOME/.config/minarca (on Linux)
     * %USERPROFILE%/AppData/Local/minarca (on Windows)
     * </pre>
     */
    public static final String CONFIG_HOME;

    /**
     * Location where to store data for minarca.
     * 
     * <pre>
     * $HOME/.local/share/minarca (on Linux)
     * %USERPROFILE%/AppData/Local/minarca (on Windows)
     * C:/Documents and Settings/username/Local Settings/Application Data/minarca (on Windows XP)
     * </pre>
     */
    public static final String DATA_HOME;

    /**
     * The user's home directory.
     * 
     * <pre>
     *  /home/username (on Linux)
     *  /root (on Linux for Root)
     *  C:/Users/username (on Windows)
     *  C:/Windows/System32/config/systemprofile (on Windows Administrator)
     * </pre>
     */
    public static final String HOME;

    /**
     * True if the user is admin (on Windows) or root (on Linux).
     */
    public static final boolean IS_ADMIN;

    /**
     * Logger used.
     */
    private static final transient Logger LOGGER;

    /**
     * Executable launch to start backup.
     */
    public static final String MINARCA_EXE;

    /**
     * Executable launch to start backup.
     */
    public static final String MINARCAUI_EXE;

    /**
     * Define temp directory.
     */
    public static final String TEMP;

    /**
     * Return a reference to the pid file for backup.
     */
    public static final File PID_FILE_BACKUP;

    /**
     * Return a reference to the pid file used for the UI.
     */
    public static final File PID_FILE_GUI;

    /**
     * Location of the status.properties file.
     */
    public static File STATUS_FILE;

    static {
        // Use a static block to declare constant value in the right order.
        LOGGER = LoggerFactory.getLogger(Compat.class);
        CHARSET_PROCESS = getProcessCharset();
        COMPUTER_NAME = getComputerName();
        IS_ADMIN = getIsAdmin();
        CONFIG_HOME = getConfigPath(IS_ADMIN);
        DATA_HOME = getDataPath(IS_ADMIN);
        PID_FILE_BACKUP = new File(DATA_HOME, "backup.pid");
        PID_FILE_GUI = new File(DATA_HOME, "gui.pid");
        TEMP = getTemp();
        HOME = getHome(IS_ADMIN);

        STATUS_FILE = new File(Compat.DATA_HOME, "status.properties");

        if (SystemUtils.IS_OS_WINDOWS) {
            if (SystemUtils.JAVA_VM_NAME.contains("64-Bit")) {
                MINARCA_EXE = "minarca64.exe";
                MINARCAUI_EXE = "minarcaui64.exe";
            } else {
                MINARCA_EXE = "minarca.exe";
                MINARCAUI_EXE = "minarcaui.exe";
            }
        } else {
            MINARCA_EXE = "minarca";
            MINARCAUI_EXE = "minarcaui";
        }

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
        throw new IllegalStateException("can't get default encoding");
    }

    /**
     * Return a computer name to represent this computer.
     * <p>
     * Current implementation gets the hostname from environment variable and use Inet interface to get a hostname.
     * 
     * @return an empty string or a hostname
     */
    private static String getComputerName() {
        // on Windows: COMPUTERNAME
        // on Linux: HOSTNAME
        try {
            String defaultValue = InetAddress.getLocalHost().getHostName();
            return getenv("COMPUTERNAME", getenv("HOSTNAME", defaultValue)).toLowerCase();
        } catch (UnknownHostException e) {
            // failed; try alternate means.
        }
        throw new IllegalStateException("can't find hostname");
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
        } else /* if (SystemUtils.IS_OS_LINUX) */ {
            if (isAdmin) {
                return "/etc/minarca";
            } else {
                return getenv("XDG_CONFIG_HOME", getHome(isAdmin) + "/.config/") + "/minarca";
            }
        }
    }

    /**
     * Return the location where to store data.
     * 
     * @param isAdmin
     *            True if admin
     * @return data folder
     */
    private static String getDataPath(boolean isAdmin) {
        // Check if data path is forced (usually used for testing).
        String path = System.getProperty("com.patrikdufresne.minarca.dataPath");
        if (path != null) {
            return path;
        }
        if (SystemUtils.IS_OS_WINDOWS) { // $NON-NLS-1$
            return getLocalAppData(isAdmin) + "/minarca";
        } else /* if (SystemUtils.IS_OS_LINUX) */ {
            if (isAdmin) {
                return "/var/lib/minarca";
            } else {
                return getenv("XDG_DATA_HOME", getHome(isAdmin) + "/.local/share/") + "/minarca";
            }
        }
    }

    /**
     * Get environment variable or return the default value if the variable is not set or empty.
     * 
     * @param variable
     *            the environment variable name
     * @param defaultValue
     *            the default value
     * @return the variable value or default value
     */
    private static String getenv(String variable, String defaultValue) {
        String value = System.getenv(variable);
        return StringUtils.defaultString(value, defaultValue);
    }

    /**
     * Return user's home.
     * 
     * @param isAdmin
     *            True if admin.
     * @return return user's home folder.
     */
    private static String getHome(boolean isAdmin) {
        if (isAdmin) {
            if (SystemUtils.IS_OS_WINDOWS) {
                return getWindowsSystemProfilePath();
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
            return getenv("LOCALAPPDATA", getHome(isAdmin) + "/Local Settings/Application Data/");
        }
        return getenv("LOCALAPPDATA", getHome(isAdmin) + "/AppData/Local/");
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
        List<File> roots = new ArrayList<File>();
        for (File f : File.listRoots()) {
            if (f.getAbsolutePath().equals("A:\\") || f.getAbsolutePath().equals("B:\\")) {
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
        throw new IllegalStateException("can't find temporary folder location");
    }

    /**
     * Return the location of the System profile.
     * 
     * @return Return a directory.
     */
    private static String getWindowsSystemProfilePath() {
        if (SystemUtils.IS_OS_WINDOWS) {
            return getenv("WINDIR", "C:/Windows") + "/System32/config/systemprofile";
        }
        throw new IllegalStateException("system profile path only availale on Windows OS");
    }

    /**
     * Print all the compat value and system properties to the logs.
     */
    public static void logValues() {
        for (Entry<Object, Object> e : System.getProperties().entrySet()) {
            LOGGER.debug(e.getKey() + " = " + e.getValue());
        }
        LOGGER.debug("CHARSET_DEFAULT = " + CHARSET_DEFAULT.name());
        LOGGER.debug("CHARSET_PROCESS = " + CHARSET_PROCESS.name());
        LOGGER.debug("COMPUTER_NAME = " + COMPUTER_NAME);
        LOGGER.debug("CONFIG_HOME = " + CONFIG_HOME);
        LOGGER.debug("DATA_HOME = " + DATA_HOME);
        LOGGER.debug("HOME = " + HOME);
        LOGGER.debug("IS_ADMIN = " + IS_ADMIN);
        LOGGER.debug("TEMP = " + TEMP);

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
            LOGGER.warn("process interrupted", e);
            Thread.currentThread().interrupt();
            throw new IllegalStateException("reg.exe process interrupted");
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
