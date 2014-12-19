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

import org.apache.commons.io.FileUtils;
import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.SystemUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.APIException;

/**
 * This utility class eases access to OS resources: scheduler, registry, execute process, directory location,
 * permission, access, os charset, etc.
 * 
 * @author ikus060
 * 
 */
public class OSUtils {

    /**
     * The name of this computer (may be null in some edge case).
     */
    public static final String COMPUTER_NAME;

    /**
     * Location where to store configuration for minarca.
     */
    public static String CONFIG_PATH;

    /**
     * True if the user is admin.
     */
    public static final boolean IS_ADMIN;

    /**
     * Logger used.
     */
    private static final transient Logger LOGGER;

    /**
     * Default charset.
     */
    public static Charset PROCESS_CHARSET;

    /**
     * The root path. Under windows it should be "C:" under linux it should be "/".
     */
    public static final String ROOT_PATH;

    /**
     * Path to system profile for Windows OS.
     * <p>
     * Under non-windows OS, this constant is null.
     */
    public static final String WINDOWS_SYSTEMPROFILE_PATH;

    static {
        // Use a static block to declare constant value in the right order.
        LOGGER = LoggerFactory.getLogger(OSUtils.class);
        COMPUTER_NAME = getComputerName();
        ROOT_PATH = getRootPath();
        PROCESS_CHARSET = getProcessCharset();
        WINDOWS_SYSTEMPROFILE_PATH = getWindowsSystemProfilePath();
        CONFIG_PATH = getAdminConfigPath();
        IS_ADMIN = getIsAdmin();
    }

    /**
     * Execute chcp process.
     * 
     * @return the code page or null
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

    /**
     * Return the location of the configuration for minarca when running with admin right.
     * 
     * @return
     */
    private static String getAdminConfigPath() {
        if (SystemUtils.IS_OS_WINDOWS) { //$NON-NLS-1$
            if (SystemUtils.IS_OS_WINDOWS_XP || SystemUtils.IS_OS_WINDOWS_2003) {
                return OSUtils.WINDOWS_SYSTEMPROFILE_PATH + "/Application Data/minarca";
            }
            return OSUtils.WINDOWS_SYSTEMPROFILE_PATH + "/AppData/Local/minarca";
        } else if (SystemUtils.IS_OS_LINUX) {
            return "/etc/minarca";
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
     * Return true if the user is admin.
     * <p>
     * This implementation make multiple assumption about administrator right. It checks if user can access the "SYSTEM"
     * registry hive. Can read-write to SYSTEM user profile.
     * 
     * @return
     */
    private static boolean getIsAdmin() {
        if (SystemUtils.IS_OS_WINDOWS) {
            // Query the SYSTEM registry hive.
            try {
                reg("query", "HKU\\S-1-5-18");
            } catch (APIException e) {
                return false;
            }
            // Check if the minarca directory can be created.
            try {
                File file = new File(CONFIG_PATH);
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
        return false;
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
        // Default to default encoding
        return Charset.defaultCharset();
    }

    /**
     * Return the home driver ( the only drive to be backup.
     * 
     * @return
     */
    private static String getRootPath() {
        if (SystemUtils.IS_OS_WINDOWS) {
            String homedrive = System.getenv("HOMEDRIVER");
            // Check if env variable contains something takt make senses
            File file = new File(homedrive + SystemUtils.PATH_SEPARATOR);
            if (file.exists() && file.isDirectory()) {
                return file.getAbsolutePath();
            }
            // At last return hardcoded value.
            return "C:\\";
        } else if (SystemUtils.IS_OS_LINUX) {
            // Under linux it's always /.
            return "/";
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
     * Execute "reg.exe" with the given arguments.
     * 
     * @param args
     *            the arguments
     * @return the output of the command.
     * @throws APIException
     *             if the process didn't complete successfully.
     */
    public static String reg(String... args) throws APIException {
        List<String> command = new ArrayList<String>();
        command.add("reg.exe");
        if (args != null) {
            command.addAll(Arrays.asList(args));
        }
        LOGGER.debug("executing {}", StringUtils.join(command, " "));
        try {
            Process p = new ProcessBuilder().command(command).redirectErrorStream(true).start();
            StreamHandler sh = new StreamHandler(p);
            sh.start();
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

}
